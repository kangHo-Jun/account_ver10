import time
import re
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
        """클립보드 복사 및 웹자료올리기 실행 [V12.0 - 저장 검증 강화]"""
        if not paste_rows:
            logger.info("ℹ️ 복사할 데이터가 없습니다")
            return False

        # 1. 클립보드 복사 (데이터 정합성 최종 체크 포함)
        processed_rows = []
        for i, row in enumerate(paste_rows):
            # D열: 입금계좌코드 (인덱스 3)
            if len(row) > 3 and not row[3]:
                logger.warning(f"   ⚠️ 행 {i+1}의 입금계좌코드 누락 발견 -> '카드사'로 자동 보정")
                row[3] = '카드사'
            processed_rows.append(row)

        import json
        lines = ["\t".join([str(cell) for cell in row]) for row in processed_rows]
        paste_text = "\r\n".join(lines)
        
        try:
            # [V10.7] 브라우저 내부에 직접 클립보드 데이터 주입
            self.page.evaluate(f"navigator.clipboard.writeText({json.dumps(paste_text)})")
            logger.info(f"📋 브라우저 내부 클립보드 데이터 주입 완료 ({len(paste_rows)}건)")
        except Exception as e:
            logger.warning(f"⚠️ 브라우저 내부 클립보드 주입 실패, 시스템 클립보드 병행: {e}")
            pyperclip.copy(paste_text)

        try:
            # 2. 웹자료올리기 팝업 열기
            logger.info("📤 '웹자료올리기' 버튼 클릭...")
            self.page.locator('#webUploader').click()
            time.sleep(3)

            # 3. 붙여넣기
            logger.info("📋 팝업 내 붙여넣기 실행 준비...")
            popup = self.page.locator('div[data-popup-id^="BulkUploadForm"]')
            
            # 그리드 영역 포커스 확보
            try:
                first_cell = popup.locator('tr[data-index="0"] td').first
                if not first_cell.is_visible():
                    first_cell = popup.locator('input.form-control').first
                
                first_cell.click(force=True)
                time.sleep(1)
                logger.info("   🎯 그리드 포커스 확보 완료")
            except Exception as e:
                logger.warning(f"   ⚠️ 포커스 확보 시도 중 예외(무시 가능): {e}")

            logger.info(f"   ⌨️ Control+V 실행 (데이터 주입 방식: Virtual Clipboard)")
            
            # [V10.6/V10.7] 저레벨 키 입력 시퀀스
            self.page.keyboard.down('Control')
            self.page.keyboard.press('v')
            self.page.keyboard.up('Control')
            
            time.sleep(3)
            
            # [V12.0] 붙여넣기 후 그리드 데이터 건수 검증
            try:
                grid_text = popup.inner_text()
                # 첫 번째 행 데이터 확인
                if processed_rows and processed_rows[0][0] not in grid_text:
                    logger.warning("⚠️ 붙여넣기 후 그리드에서 데이터 미감지 -> 폴백(Type) 시도")
                    first_cell.click()
                    self.page.keyboard.type(paste_text)
                    time.sleep(3)
            except: pass

            # 4. 저장 (F8) - [V12.1] 팝업 정리 후 저장
            if TEST_MODE:
                logger.warning("⛔ 테스트 모드: F8 저장 생략")
                return True
            
            logger.info("💾 F8 저장 실행...")
            
            # [V12.1] F8 전에 현재 팝업 개수 확인
            try:
                existing_popups = self.page.locator('div.ui-dialog').count()
                logger.info(f"   📊 저장 전 팝업 개수: {existing_popups}")
            except:
                existing_popups = 0
            
            self.page.keyboard.press('F8')
            
            # [V12.1] 저장 처리 시간 확보
            logger.info("   ⏳ 저장 처리 대기 중...")
            time.sleep(3)
            
            # 5. 저장 결과 팝업 대기 및 분석 [V12.1 개선]
            try:
                # 새로운 팝업이 나타날 때까지 대기 (최대 15초)
                for i in range(15):
                    time.sleep(1)
                    current_popups = self.page.locator('div.ui-dialog').count()
                    if current_popups > existing_popups:
                        logger.info(f"   ✅ 새 팝업 감지 ({i+1}초 후)")
                        break
                
                # 가장 최근 팝업 선택
                result_popup = self.page.locator('div.ui-dialog').last
                
                if not result_popup.is_visible():
                    logger.warning("⚠️ 저장 결과 팝업을 찾을 수 없음 - 저장 성공으로 간주")
                    return True
                
                msg = result_popup.inner_text()
                logger.info(f"📢 저장 결과 팝업: {msg.replace(chr(10), ' ')[:200]}...")
                
                # [V12.1] 실패 키워드 우선 검사
                fail_keywords = ["실패", "오류", "에러", "(필수)", "확인바랍니다", "입력하세"]
                if any(k in msg for k in fail_keywords) and "실패 : 0건" not in msg:
                    logger.error(f"❌ 업로드 실패 감지!")
                    self.page.screenshot(path=f"logs/upload_fail_{int(time.time())}.png")
                    # 팝업 정리
                    try:
                        close_btn = result_popup.locator('button:has-text("닫기"), a:has-text("닫기")').first
                        if close_btn.is_visible():
                            close_btn.click()
                    except: pass
                    return False
                
                # [V12.1] 성공 패턴 확인: "성공 : N건" 또는 "성공: N건"
                success_pattern = r"성공\s*[:：]\s*(\d+)\s*건"
                match = re.search(success_pattern, msg)
                
                if match:

                    success_count = int(match.group(1))
                    logger.info(f"✅ 저장 성공 확정: {success_count}건 업로드 완료")
                    
                    # 닫기 버튼 클릭
                    try:
                        close_btn = result_popup.locator('button:has-text("닫기"), a:has-text("닫기"), .ui-dialog-titlebar-close').first
                        if close_btn.is_visible():
                            close_btn.click()
                            logger.info("   ✅ 결과 팝업 닫기 완료")
                    except: pass
                    
                    time.sleep(1)
                    # 메인 팝업도 정리
                    if popup.is_visible():
                        self.page.keyboard.press('Escape')
                    
                    return True
                else:
                    # [V12.0] 성공 메시지 없으면 무조건 실패 처리
                    logger.error("❌ 저장 실패: '성공 : N건' 메시지를 찾을 수 없음")
                    self.page.screenshot(path=f"logs/save_no_success_{int(time.time())}.png")
                    
                    # 팝업 정리 시도
                    try:
                        close_btn = result_popup.locator('button:has-text("닫기"), a:has-text("닫기")').first
                        if close_btn.is_visible():
                            close_btn.click()
                    except: pass
                    
                    return False
                
            except Exception as e:
                logger.error(f"❌ 저장 결과 확인 실패: {e}")
                self.page.screenshot(path=f"logs/save_error_{int(time.time())}.png")
                
                # ESC로 화면 정리
                self.page.keyboard.press('Escape')
                time.sleep(0.5)
                self.page.keyboard.press('Escape')
                
                return False

        except Exception as e:
            logger.error(f"❌ 업로드 과정 오류: {e}")
            return False
