import time
from core.logger import logger
from utils.config import LOGIN_URL, CREDENTIALS

class LoginModule:
    def __init__(self, page):
        self.page = page

    def login(self) -> bool:
        """이카운트 로그인"""
        try:
            logger.info(f"[LOGIN] 로그인 페이지 이동: {LOGIN_URL}")
            self.page.goto(LOGIN_URL, timeout=30000)
            time.sleep(2)

            # 회사코드 입력
            logger.info("   회사코드 입력...")
            self.page.locator('input[name="com_code"]').fill(CREDENTIALS.get('company_code', ''))

            # 아이디 입력
            logger.info("   아이디 입력...")
            self.page.locator('input[name="id"]').fill(CREDENTIALS.get('username', ''))

            # 비밀번호 입력
            logger.info("   비밀번호 입력...")
            self.page.locator('input[name="passwd"]').fill(CREDENTIALS.get('password', ''))

            time.sleep(1)

            # 로그인 버튼 클릭
            logger.info("   로그인 버튼 클릭...")
            self.page.locator('button[id="save"]').click()

            # 로그인 완료 대기
            self.page.wait_for_url(
                lambda url: not url.startswith('https://login.ecount.com/'), 
                timeout=15000
            )

            if self.page.url.startswith('https://login.ecount.com/'):
                logger.error("[ERROR] 로그인 실패")
                return False

            logger.info("[OK] 로그인 성공")
            time.sleep(5)
            
            # 여기서 세션 저장을 시도할 수 있도록 브라우저 매니저의 기능 활용 유도
            # (현재 구조상 브라우저 매니저가 세션을 관리하므로 main.py에서 처리하는 것이 더 깔끔함)
            return True

        except Exception as e:
            logger.error(f"[ERROR] 로그인 오류: {e}")
            return False
