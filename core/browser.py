import json
import time
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

from core.logger import logger
from utils.config import HEADLESS_MODE


ERP_BASE_URL = "https://loginab.ecount.com/ec5/view/erp?w_flag=1"


class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session_file = Path("sessions/session.json")

    def get_erp_frame(self):
        """Return the ERP frame when the wrapper page is in use."""
        if not self.page:
            return None
        for frame in self.page.frames:
            if "ec5/view/erp" in frame.url:
                return frame
        return self.page

    def _is_bad_session_url(self, url: str) -> bool:
        return (
            not url
            or "login.ecount.com" in url
            or "app.login/erp_login" in url
            or "ec5/view/erp" not in url
        )

    def _erp_url_from_cookies(self):
        if not self.context:
            return None

        for cookie in self.context.cookies():
            if cookie.get("name") != "ECOUNT_SessionId":
                continue

            raw_value = cookie.get("value", "")
            session_id = raw_value.split("=", 1)[0]
            if session_id:
                return f"{ERP_BASE_URL}&ec_req_sid={session_id}"

        return None

    def _recover_erp_shell_from_cookie(self) -> bool:
        direct_url = self._erp_url_from_cookies()
        if not direct_url:
            logger.warning("[SESSION] ERP session cookie not found for direct shell recovery")
            return False

        try:
            logger.warning(f"[SESSION] opening ERP shell directly from session cookie: {direct_url}")
            self.page.goto(direct_url, wait_until="load", timeout=30000)
            time.sleep(5)
            return True
        except Exception as e:
            logger.warning(f"[SESSION] direct ERP shell recovery failed: {e}")
            return False

    def wait_for_erp_shell(self, timeout=60000, allow_recovery=True) -> bool:
        """Wait until the real ERP shell frame is loaded."""
        if not self.page:
            return False

        deadline = time.time() + (timeout / 1000)
        while time.time() < deadline:
            current_url = self.page.url
            erp_target = self.get_erp_frame()
            erp_url = erp_target.url if erp_target else current_url

            if "ec5/view/erp" in erp_url and "app.login/erp_login" not in erp_url:
                logger.info(f"[OK] ERP shell ready (URL: {erp_url})")
                return True

            if "app.login/erp_login" in current_url:
                logger.info("[SESSION] waiting for ERP frame from login handoff page")

            time.sleep(2)

        if allow_recovery and "app.login/erp_login" in self.page.url:
            if self._recover_erp_shell_from_cookie():
                return self.wait_for_erp_shell(timeout=20000, allow_recovery=False)

        frame_urls = [frame.url for frame in self.page.frames]
        logger.warning(
            f"[WARN] ERP shell not ready (current URL: {self.page.url}, frames: {frame_urls})"
        )
        return False

    def start(self, headless=None):
        """Start browser."""
        if headless is None:
            headless = HEADLESS_MODE

        logger.info(f"[BROWSER] browser starting... (headless={headless})")

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                slow_mo=300,
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            logger.info("[OK] browser started")
            return self.page
        except Exception as e:
            logger.error(f"[ERROR] browser start failed: {e}")
            self.close()
            raise

    def load_session(self) -> bool:
        """Load saved ERP session."""
        if not self.session_file.exists():
            logger.info("[INFO] saved session does not exist")
            return False

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            if "cookies" not in session_data:
                return False

            self.context.add_cookies(session_data["cookies"])
            logger.info("[SESSION] cookies loaded")

            saved_url = session_data.get("url", ERP_BASE_URL)
            if self._is_bad_session_url(saved_url):
                logger.warning(f"[SESSION] invalid saved URL ignored: {saved_url}")
                self.context.clear_cookies()
                return False

            if self.page.is_closed():
                self.page = self.context.new_page()

            logger.info(f"[SESSION] navigating to saved URL: {saved_url}")
            self.page.goto(saved_url, wait_until="load", timeout=30000)
            time.sleep(5)

            current_url = self.page.url
            if self.wait_for_erp_shell(timeout=30000):
                return True

            logger.warning(f"[WARN] saved session invalid (current URL: {current_url})")
            self.context.clear_cookies()
            return False
        except Exception as e:
            logger.error(f"[ERROR] session load failed: {e}")
            return False

    def save_session(self):
        """Save current ERP session."""
        try:
            if self.page.url.startswith("https://login.ecount.com/"):
                logger.warning(f"[SESSION] skip saving login URL: {self.page.url}")
                return

            cookies = self.context.cookies()
            erp_target = self.get_erp_frame()
            target_url = erp_target.url if erp_target else self.page.url
            if self._is_bad_session_url(target_url):
                logger.warning(f"[SESSION] skip saving invalid ERP target URL: {target_url}")
                return

            session_data = {
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "url": target_url,
            }

            self.session_file.parent.mkdir(exist_ok=True)
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info("[SAVE] session saved")
        except Exception as e:
            logger.error(f"[ERROR] session save failed: {e}")

    def close(self):
        """Close browser and Playwright resources."""
        logger.info("[STOP] browser cleanup starting...")
        try:
            if self.page:
                try:
                    self.page.close()
                except Exception:
                    pass
                self.page = None
            if self.context:
                try:
                    self.context.close()
                except Exception:
                    pass
                self.context = None
            if self.browser:
                try:
                    self.browser.close()
                except Exception:
                    pass
                self.browser = None
            if self.playwright:
                try:
                    self.playwright.stop()
                except Exception:
                    pass
                self.playwright = None

            logger.info("[OK] browser and Playwright cleaned up")
        except Exception as e:
            logger.error(f"[WARN] browser cleanup error: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def shutdown(self):
        """Final shutdown."""
        logger.info("[SHUTDOWN] final resource cleanup...")
        self.close()
