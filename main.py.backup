"""
이카운트 웹 자동화 V9.0 - 고도의 모듈화 아키텍처
============================================================
- 책임 분리: core(브라우저, 로그), modules(로그인, 조회, 변환, 업로드), utils(설정)
- 확장성 및 유지보수성 향상
"""

import pandas as pd
import sys
import time
import ctypes
import traceback
import os
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
        self.lock_file = Path("runtime.lock")
        self.lock_fp = None

        # 프로세스 락 확보 (중복 실행 방지)
        if not self.acquire_lock():
            print("[ERROR] 이미 실행 중인 프로세스가 있습니다. 프로그램을 종료합니다.")
            sys.exit(1)

        self.browser = BrowserManager()
        self.notifier = NotifierModule()
        self.stats = {
            "total": 0,
            "success": 0,
            "failure": 0,
            "count": 0,
            "cancellations": 0  # 취소 거래 건수
        }
        self.is_keep_alive = False
        self.daily_report_sent = False  # 일일 보고서 발송 여부

    def acquire_lock(self):
        """프로세스 중복 실행 방지 (Windows)"""
        try:
            # 락 파일이 이미 있는지 확인
            if self.lock_file.exists():
                with open(self.lock_file, 'r') as f:
                    old_pid = f.read().strip()

                # PID가 유효한지 확인
                try:
                    old_pid_int = int(old_pid)
                    # Windows에서 프로세스 존재 여부 확인
                    import subprocess
                    result = subprocess.run(
                        ['tasklist', '/FI', f'PID eq {old_pid_int}'],
                        capture_output=True,
                        text=True
                    )
                    # tasklist 출력에 PID가 포함되어 있으면 프로세스가 실행 중
                    if str(old_pid_int) in result.stdout:
                        logger.error(f"[LOCK] 이미 실행 중인 프로세스 (PID: {old_pid_int})")
                        return False
                    else:
                        # 프로세스 없음 → 락 파일 삭제
                        logger.warning(f"[LOCK] 이전 프로세스 (PID: {old_pid_int}) 종료됨. 락 파일 삭제")
                        self.lock_file.unlink()
                except (ValueError, subprocess.SubprocessError) as e:
                    # PID 파싱 실패 또는 tasklist 실패 → 락 파일 삭제
                    logger.warning(f"[LOCK] 락 파일 검증 실패: {e}. 락 파일 삭제")
                    self.lock_file.unlink()

            # 새 락 파일 생성
            current_pid = os.getpid()
            with open(self.lock_file, 'w') as f:
                f.write(str(current_pid))

            logger.info(f"[LOCK] 프로세스 락 확보 (PID: {current_pid})")
            return True
        except Exception as e:
            logger.error(f"[LOCK] 락 파일 생성 실패: {e}")
            return False

    def release_lock(self):
        """프로세스 종료 시 락 해제"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info("[LOCK] 프로세스 락 해제")
        except Exception as e:
            logger.warning(f"[LOCK] 락 파일 삭제 실패: {e}")

    def heartbeat(self):
        """프로세스 생존 신호 기록"""
        try:
            heartbeat_file = Path("heartbeat.txt")
            with open(heartbeat_file, 'w', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()}\n")
                f.write(f"PID: {os.getpid()}\n")
                f.write(f"Stats: {self.stats}\n")
        except Exception as e:
            logger.warning(f"[HEARTBEAT] 하트비트 기록 실패: {e}")

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
                    logger.info("[SYSTEM] 시스템 절전 모드 방지 기능 활성화")
            else:
                if self.is_keep_alive:
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                    self.is_keep_alive = False
                    logger.info("[SLEEP] 시스템 절전 모드 방지 기능 해제")
        except Exception as e:
            logger.warning(f"[WARN] 절전 모드 설정 변경 실패: {e}")

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
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] [CYCLE] 자동화 사이클 시작")
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
                logger.info("[INFO] 처리할 데이터가 없습니다.")
                self.stats["success"] += 1
                return

            # 4. 데이터 변환 (실시간 내역 전달)
            transformer = TransformerModule()
            paste_rows, new_keys, cycle_stats = transformer.transform(raw_data, reflected_nos=reflected_nos)
            
            if not paste_rows:
                logger.info("[INFO] 업로드할 새 데이터가 없습니다.")
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
                    logger.info(f"[RECORD] {len(new_keys)}건 업로드 기록 저장")
                
                self.stats["success"] += 1
                self.stats["count"] += len(paste_rows)
                self.stats["cancellations"] += cycle_stats.get("cancellations", 0)
                logger.info(f"[OK] 사이클 완료 ({len(paste_rows)}건 처리)")
            else:
                raise Exception("업로드 과정 중 오류")

        except Exception as e:
            self.stats["failure"] += 1
            err_msg = f"[ERROR] 사이클 오류: {str(e)}"
            logger.error(err_msg)
            # 에러 발생 시 이메일 알림
            self.notifier.send_error_notification(err_msg, traceback.format_exc())
        
        finally:
            # [지능형 제어] 사이클 종료 시 무조건 브라우저를 닫아 화면을 정리함
            try:
                self.browser.close()
            except:
                pass

            # 사이클 종료 후 로그 파일 로테이션 (운영 모드에서만)
            if not TEST_MODE:
                logger.rotate_log_file()

    def run(self):
        try:
            logger.info("=" * 60)
            logger.info(f"[START] 이카운트 웹 자동화 V9.5 실행 (모드: {MODE})")
            logger.info("=" * 60)

            if TEST_MODE:
                # 테스트 모드는 1회 실행 후 대기
                self.single_cycle()
                logger.info("[TEST] 테스트 완료. 화면을 유지합니다.")
                input(">>> Enter를 누르면 브라우저를 종료합니다...")
                self.browser.close()
            else:
                # 운영 모드: 무한 루프
                interval = SCHEDULE_CONFIG.get("interval_minutes", 30) * 60
                try:
                    # 프로그램 실행 중에는 항상 절전 방지 활성화
                    self.set_keep_alive(True)

                    # 프로그램 시작 날짜 기록
                    start_date = datetime.now().date()

                    while True:
                        # 프로세스 생존 신호 기록
                        self.heartbeat()

                        now = datetime.now()
                        current_time = now.strftime("%H:%M")
                        current_date = now.date()

                        # 날짜가 바뀌고 업무시간(06:00) 이후가 되면 프로그램 재시작 (로그 파일 갱신)
                        if current_date > start_date and current_time >= "06:00":
                            logger.info("[RESTART] 새로운 날 시작 - 프로그램 재시작 (로그 파일 갱신)")
                            self.set_keep_alive(False)
                            self.browser.shutdown()
                            logger.info("=" * 60)
                            sys.exit(0)

                        # 17:45 이후이고 아직 보고서를 보내지 않았다면 발송
                        if current_time >= "17:45" and not self.daily_report_sent and self.stats["total"] > 0:
                            logger.info("[REPORT] 일일 요약 리포트 발송 시간 (17:45)")
                            self.notifier.send_summary_notification(self.stats)
                            self.daily_report_sent = True

                        if self.is_work_time():
                            self.single_cycle()
                            logger.info(f"[WAIT] {interval//60}분 대기 중...")
                            time.sleep(interval)
                        else:
                            # 다음 날을 위해 통계 및 플래그 초기화
                            if self.stats["total"] > 0 or self.daily_report_sent:
                                logger.info("[SLEEP] 업무 시간 종료. 통계 초기화")
                                self.stats = {
                                    "total": 0,
                                    "success": 0,
                                    "failure": 0,
                                    "count": 0,
                                    "cancellations": 0
                                }
                                self.daily_report_sent = False

                            logger.info(f"[SLEEP] 업무 시간 외 (다음 확인 10분 후)")
                            time.sleep(600)
                finally:
                    self.set_keep_alive(False) # 프로그램 종료 시 무조건 절전 허용 복구
                    self.browser.shutdown()  # Playwright 완전 종료
        finally:
            # 프로그램 종료 시 반드시 락 해제
            self.release_lock()

if __name__ == "__main__":
    orchestrator = EcountAutomationOrchestrator()
    orchestrator.run()
