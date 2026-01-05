"""
이카운트 웹 자동화 V9.0 - 고도의 모듈화 아키텍처
============================================================
- 책임 분리: core(브라우저, 로그), modules(로그인, 조회, 변환, 업로드), utils(설정)
- 확장성 및 유지보수성 향상
"""

import pandas as pd
import time
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
            excel_path = Path("양식.xlsx")
            
            if excel_path.exists():
                logger.info(f"📊 엑셀 파일 감지: {excel_path}")
                df = pd.read_excel(excel_path, skiprows=1)
                raw_data = []
                for _, row in df.iterrows():
                    d_val = str(row.get('결제요청일시', '')).strip()
                    if not d_val or d_val in ['nan', 'None']: continue
                    raw_data.append({
                        'date_raw': d_val,
                        'customer': str(row.get('고객명', '')).strip(),
                        'amount': str(row.get('결제금액', '')).strip(),
                        'account': str(row.get('매입지명', '')).strip(),
                        'status': str(row.get('결제상태', '')).strip()
                    })
            else:
                if not reader.navigate_to_payment_query():
                    raise Exception("결제조회 페이지 이동 실패")
                if not reader.click_unreflected_filter():
                    raise Exception("미반영 필터 클릭 실패")
                raw_data = reader.read_payment_data()

            if not raw_data:
                logger.info("ℹ️ 처리할 데이터가 없습니다.")
                self.stats["success"] += 1
                return

            # 4. 데이터 변환
            transformer = TransformerModule()
            paste_rows, new_keys = transformer.transform(raw_data)
            
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
            
            # 테스트 모드가 아니면 브라우저 재시작을 위해 리셋 고려 가능
            # 여기서는 단순히 다음 사이클 대기

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
            while True:
                if self.is_work_time():
                    self.single_cycle()
                    logger.info(f"💤 {interval//60}분 대기 중...")
                    time.sleep(interval)
                else:
                    # 업무 종료 시 요약 리포트 발송 (오늘 한 번도 안 보냈다면)
                    if self.stats["total"] > 0:
                        logger.info("🌙 업무 시간 종료. 일일 요약 리포트를 발송합니다.")
                        self.notifier.send_summary_notification(self.stats)
                        # 통계 초기화 (다음 날을 위해)
                        self.stats = {"total": 0, "success": 0, "failure": 0, "count": 0}
                    
                    logger.info(f"🌙 업무 시간 외 (다음 확인 10분 후)")
                    time.sleep(600)

if __name__ == "__main__":
    orchestrator = EcountAutomationOrchestrator()
    orchestrator.run()
