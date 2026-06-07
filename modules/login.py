import time
from core.logger import logger
from utils.config import LOGIN_URL, CREDENTIALS


class LoginModule:
    def __init__(self, page, browser_manager=None):
        self.page = page
        self.browser_manager = browser_manager

    def _get_erp_target(self):
        if self.browser_manager:
            return self.browser_manager.get_erp_frame()
        return self.page

    def login(self) -> bool:
        """Ecount login."""
        try:
            logger.info(f"[LOGIN] 로그인 페이지 이동: {LOGIN_URL}")
            self.page.goto(LOGIN_URL, timeout=30000)
            time.sleep(2)

            logger.info("   회사코드 입력...")
            self.page.locator('input#com_code').fill(CREDENTIALS.get('company_code', ''))

            logger.info("   아이디 입력...")
            self.page.locator('input#id').fill(CREDENTIALS.get('username', ''))

            logger.info("   비밀번호 입력...")
            self.page.locator('input#passwd').fill(CREDENTIALS.get('password', ''))

            time.sleep(1)

            logger.info("   로그인 버튼 클릭...")
            self.page.locator('button[id=\"save\"]').click()

            self.page.wait_for_url(
                lambda url: not url.startswith('https://login.ecount.com/'),
                timeout=15000,
            )

            if self.page.url.startswith('https://login.ecount.com/'):
                logger.error("[ERROR] 로그인 실패")
                return False

            logger.info("[OK] 로그인 성공")

            try:
                erp_target = self._get_erp_target()
                erp_target.wait_for_selector('a#link_depth4_MENUTREE_002905', timeout=30000)
                logger.info("[OK] ERP 셸 안정화 확인 - 메뉴 링크 감지")
            except Exception:
                logger.warning("[WARN] ERP 셸 메뉴 링크 미감지 - 5초 추가 대기")
                time.sleep(5)

            return True

        except Exception as e:
            logger.error(f"[ERROR] 로그인 오류: {e}")
            return False
