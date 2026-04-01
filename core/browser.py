import json
import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from core.logger import logger
from utils.config import HEADLESS_MODE

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session_file = Path("sessions/session.json")

    def start(self, headless=None):
        """브라우저 시작"""
        if headless is None:
            headless = HEADLESS_MODE

        # [강력 조치] 시작 전 잔류 Chrome 프로세스가 있다면 정리 (환경 정비)
        try:
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
            logger.info("[INIT] 잔류 Chrome 프로세스 사전 정리 완료")
        except:
            pass

        logger.info(f"[BROWSER] 브라우저 시작 중... (headless={headless})")

        # Playwright 인스턴스를 매번 새로 생성 (event loop 문제 해결)
        try:
            self.playwright = sync_playwright().start()

            # 브라우저는 매번 새로 생성 (리소스 정리)
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                slow_mo=300,
                args=['--disable-dev-shm-usage', '--no-sandbox'] # 리소스 제한 대응
            )

            self.context = self.browser.new_context(
                permissions=['clipboard-read', 'clipboard-write']
            )
            self.page = self.context.new_page()
            logger.info("[OK] 브라우저 시작 완료")
            return self.page
        except Exception as e:
            logger.error(f"[ERROR] 브라우저 시작 실패: {e}")
            self.close()
            raise

    def load_session(self) -> bool:
        """저장된 세션 로드"""
        if not self.session_file.exists():
            logger.info("[INFO] 저장된 세션 없음")
            return False

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            if 'cookies' in session_data:
                self.context.add_cookies(session_data['cookies'])
                logger.info("[SESSION] 세션 쿠키 로드 완료")

                saved_url = session_data.get('url', 'https://loginab.ecount.com/ec5/view/erp')
                
                # 페이지가 닫혀있는지 확인 후 재생성
                if self.page.is_closed():
                    self.page = self.context.new_page()

                logger.info(f"[SESSION] 세션 URL 접속 시도: {saved_url}")
                self.page.goto(saved_url, wait_until='load', timeout=30000)
                time.sleep(5) 

                current_url = self.page.url
                if "app.login" not in current_url and "login.ecount.com" not in current_url:
                    logger.info(f"[OK] 세션 유효함 (URL: {current_url})")
                    return True
                else:
                    logger.warning(f"[WARN] 세션 만료됨 (로그인 페이지 감지: {current_url})")
                    self.context.clear_cookies()
                    return False
            return False
        except Exception as e:
            logger.error(f"[ERROR] 세션 로드 실패: {e}")
            return False

    def save_session(self):
        """현재 세션 저장"""
        try:
            if self.page.url.startswith('https://login.ecount.com/'):
                return

            cookies = self.context.cookies()
            session_data = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'url': self.page.url
            }

            self.session_file.parent.mkdir(exist_ok=True)
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info("[SAVE] 세션 저장 완료")
        except Exception as e:
            logger.error(f"[ERROR] 세션 저장 실패: {e}")

    def close(self):
        """브라우저 및 Playwright 완전 종료"""
        logger.info("[STOP] 브라우저 종료 시퀀스 시작...")
        try:
            if self.page:
                try: self.page.close()
                except: pass
                self.page = None
            if self.context:
                try: self.context.close()
                except: pass
                self.context = None
            if self.browser:
                try: self.browser.close()
                except: pass
                self.browser = None
            if self.playwright:
                try: self.playwright.stop()
                except: pass
                self.playwright = None

            # [강력 조치] 좀비 Chrome 프로세스 강제 정리
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
            
            logger.info("[OK] 브라우저 및 Playwright 완전 정리 완료")
        except Exception as e:
            logger.error(f"[WARN] 브라우저 종료 중 예기치 않은 오류: {e}")
        finally:
            # 상태 초기화 보장
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def shutdown(self):
        """애플리케이션 종료 시 최종 정리"""
        logger.info("[SHUTDOWN] 전체 시스템 자원 정리...")
        self.close()
