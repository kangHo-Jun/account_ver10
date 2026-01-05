import time
import pyperclip
from core.logger import logger
from utils.config import DEPOSIT_REPORT_HASH, TEST_MODE

class UploaderModule:
    def __init__(self, page):
        self.page = page

    def navigate_to_deposit_report(self) -> bool:
        """입금보고서 페이지로 이동"""
        try:
            logger.info("📄 입금보고서 페이지로 이동...")
            js_code = f"window.location.hash = '{DEPOSIT_REPORT_HASH}';"
            self.page.evaluate(js_code)
            time.sleep(5)
            return True
        except Exception as e:
            logger.error(f"❌ 페이지 이동 실패: {e}")
            return False

    def upload(self, paste_rows: list) -> bool:
        """클립보드 복사 및 웹자료올리기 실행"""
        if not paste_rows:
            logger.info("ℹ️ 복사할 데이터가 없습니다")
            return False

        # 1. 클립보드 복사
        lines = ["\t".join([str(cell) for cell in row]) for row in paste_rows]
        pyperclip.copy("\r\n".join(lines))
        logger.info(f"📋 {len(paste_rows)}건 클립보드 복사 완료")

        try:
            # 2. 웹자료올리기 팝업 열기
            logger.info("📤 '웹자료올리기' 버튼 클릭...")
            self.page.locator('#webUploader').click()
            time.sleep(3)

            # 3. 붙여넣기
            logger.info("📋 팝업 내 붙여넣기 실행...")
            popup = self.page.locator('div[data-popup-id^="BulkUploadForm"]')
            first_cell = popup.locator('input.form-control').first
            first_cell.click(force=True)
            self.page.keyboard.press('Control+v')
            time.sleep(2)

            # 4. 저장 (F8)
            if TEST_MODE:
                logger.warning("⛔ 테스트 모드: F8 저장 생략")
                return True
            
            logger.info("💾 F8 저장 실행...")
            self.page.keyboard.press('F8')
            time.sleep(3)
            return True

        except Exception as e:
            logger.error(f"❌ 업로드 과정 오류: {e}")
            return False
