"""
이카운트 웹 자동화 V9.0 - 고도의 모듈화 아키텍처
============================================================
- 책임 분리: core(브라우저, 로그), modules(로그인, 조회, 변환, 업로드), utils(설정)
- 확장성 및 유지보수성 향상
"""

import pandas as pd
import time
import ctypes
import traceback
from datetime import datetime
from pathlib import Path
from core.browser import BrowserManager
from core.logger import logger
from modules.login import LoginModule
from modules.reader import ReaderModule
from modules.transformer import TransformerModule
from modules.uploader import UploaderModule
from modules.notifier import NotifierModule
from utils.config import (
    TEST_MODE, MODE, SCHEDULE_CONFIG, URLS
)

class EcountAutomationOrchestrator:
    def __init__(self):
        self.browser = BrowserManager()
        self.notifier = NotifierModule()
        self.stats = {"total": 0, "success": 0, "failure": 0, "count": 0}
        self.is_keep_alive = False

    def set_keep_alive(self, enable=True):
        """Windows API를 호출하여 절전모드 진입 방지 또는 해제"""
        try:
            # ES_CONTINUOUS: 설정 지속
            # ES_SYSTEM_REQUIRED: 시스템 절전 방지
            # ES_AWAYMODE_REQUIRED: 어웨이 모드 (선택적)
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            
            if enable:
                if not self.is_keep_alive:
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
                    self.is_keep_alive = True
                    logger.info("🛡️ 시스템 절전 모드 방지 기능 활성화")
            else:
                if self.is_keep_alive:
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                    self.is_keep_alive = False
                    logger.info("🌙 시스템 절전 모드 방지 기능 해제")
        except Exception as e:
            logger.warning(f"⚠️ 절전 모드 설정 변경 실패: {e}")

    def is_work_time(self):
        """현재 시간이 업무 시간인지 확인 (06:00 ~ 18:00)"""
        if not SCHEDULE_CONFIG.get("enabled", True):
            return True
        
        now = datetime.now()
        # 주말 제외 (설계서 기준 토요일 14:00까지이나 일단 간단히 시간 위주)
        if now.weekday() == 6:  # 일요일
            return False
            
        current_time = now.strftime("%H:%M")
        start_time = SCHEDULE_CONFIG.get("work_hours", {}).get("start", "06:00")
        end_time = SCHEDULE_CONFIG.get("work_hours", {}).get("end", "18:00")
        
        return start_time <= current_time <= end_time

    def single_cycle(self):
        """단일 자동화 사이클 실행"""
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 자동화 사이클 시작")
        self.stats["total"] += 1
        
        try:
            # 1. 브라우저 시작
            page = self.browser.start()

            # 2. 세션 로드 또는 로그인
            if not self.browser.load_session():
                page = self.browser.page 
                login_mod = LoginModule(page)
                if not login_mod.login():
                    raise Exception("로그인 실패")
                self.browser.save_session()
            
            page = self.browser.page

            # 3. 데이터 읽기
            reader = ReaderModule(page)
            
            # [V10] 실시간 ERP 회계반영 내역 수집 (중복 제로 달성용)
            if not reader.navigate_to_payment_query():
                raise Exception("결제조회 페이지 이동 실패")
            
            # get_reflected_status 내부에서 '회계반영' 확인 후 자동으로 '미반영'으로 복구함
            reflected_nos = reader.get_reflected_status()
            
            raw_data = reader.read_payment_data()

            if not raw_data:
                logger.info("ℹ️ 처리할 데이터가 없습니다.")
                self.stats["success"] += 1
                return

            # 4. 데이터 변환 (실시간 내역 전달)
            transformer = TransformerModule()
            paste_rows, new_keys = transformer.transform(raw_data, reflected_nos=reflected_nos)
            
            if not paste_rows:
                logger.info("ℹ️ 업로드할 새 데이터가 없습니다.")
                self.stats["success"] += 1
                return

            # 5. 업로드
            uploader = uploader = UploaderModule(page)
            if not uploader.navigate_to_deposit_report():
                raise Exception("입금보고서 페이지 이동 실패")
            
            if uploader.upload(paste_rows):
                if not TEST_MODE:
                    uploaded_records = transformer.load_uploaded_records()
                    uploaded_records.update(new_keys)
                    transformer.save_uploaded_records(uploaded_records)
                    logger.info(f"📝 {len(new_keys)}건 업로드 기록 저장")
                
                self.stats["success"] += 1
                self.stats["count"] += len(paste_rows)
                logger.info(f"✅ 사이클 완료 ({len(paste_rows)}건 처리)")
            else:
                raise Exception("업로드 과정 중 오류")

        except Exception as e:
            self.stats["failure"] += 1
            err_msg = f"❌ 사이클 오류: {str(e)}"
            logger.error(err_msg)
            # 에러 발생 시 이메일 알림
            self.notifier.send_error_notification(err_msg, traceback.format_exc())
        
        finally:
            # [지능형 제어] 사이클 종료 시 무조건 브라우저를 닫아 화면을 정리함
            try:
                self.browser.close()
            except:
                pass

    def run(self):
        logger.info("=" * 60)
        logger.info(f"🚀 이카운트 웹 자동화 V9.5 실행 (모드: {MODE})")
        logger.info("=" * 60)

        if TEST_MODE:
            # 테스트 모드는 1회 실행 후 대기
            self.single_cycle()
            logger.info("⚠️ 테스트 완료. 화면을 유지합니다.")
            input(">>> Enter를 누르면 브라우저를 종료합니다...")
            self.browser.close()
        else:
            # 운영 모드: 무한 루프
            interval = SCHEDULE_CONFIG.get("interval_minutes", 30) * 60
            try:
                while True:
                    if self.is_work_time():
                        self.set_keep_alive(True)  # 업무 시간 중 절전 방지
                        self.single_cycle()
                        logger.info(f"💤 {interval//60}분 대기 중...")
                        time.sleep(interval)
                    else:
                        self.set_keep_alive(False) # 업무 시간 종료 시 절전 허용
                        # 업무 종료 시 요약 리포트 발송 (오늘 한 번도 안 보냈다면)
                        if self.stats["total"] > 0:
                            logger.info("🌙 업무 시간 종료. 일일 요약 리포트를 발송합니다.")
                            self.notifier.send_summary_notification(self.stats)
                            # 통계 초기화 (다음 날을 위해)
                            self.stats = {"total": 0, "success": 0, "failure": 0, "count": 0}
                        
                        logger.info(f"🌙 업무 시간 외 (다음 확인 10분 후)")
                        time.sleep(600)
            finally:
                self.set_keep_alive(False) # 프로그램 종료 시 무조건 절전 허용 복구

if __name__ == "__main__":
    orchestrator = EcountAutomationOrchestrator()
    orchestrator.run()
