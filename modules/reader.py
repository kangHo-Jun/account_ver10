import time
import pandas as pd
from pathlib import Path
from core.logger import logger
from utils.config import PAYMENT_QUERY_HASH

class ReaderModule:
    def __init__(self, page):
        self.page = page

    def navigate_to_payment_query(self) -> bool:
        """결제내역조회 페이지로 이동"""
        try:
            logger.info("📄 결제내역조회 페이지로 이동...")
            js_code = f"window.location.hash = '{PAYMENT_QUERY_HASH}';"
            self.page.evaluate(js_code)
            
            # 페이지 로딩 대기
            time.sleep(10)
            return True
        except Exception as e:
            logger.error(f"❌ 페이지 이동 실패: {e}")
            return False

    def click_unreflected_filter(self) -> bool:
        """'미반영' 필터 클릭"""
        try:
            logger.info("🔘 '미반영' 버튼 클릭 시도...")
            
            # 1. 프레임 목록 출력 및 로드 대기
            time.sleep(5)
            logger.info(f"   현재 페이지 URL: {self.page.url}")
            frames = self.page.frames
            logger.info(f"   감지된 프레임 수: {len(frames)}")
            for i, f in enumerate(frames):
                logger.info(f"   - 프레임 {i}: {f.name} ({f.url[:50]}...)")

            # 2. 여러 셀렉터 후보군 시도 (모든 프레임 대상)
            selectors = [
                'a#tabUnReflect',
                '#tabUnReflect',
                'text="미반영"',
                '.unreflected', # 혹시 모를 클래스명
                'li[id*="tabUnReflect"] a'
            ]
            
            target_element = None
            # 메인 페이지 및 모든 프레임에서 조회
            for frame in self.page.frames:
                for selector in selectors:
                    try:
                        el = frame.locator(selector).first
                        if el.is_visible(timeout=3000):
                            target_element = el
                            logger.info(f"   ✅ 매칭 발견! 프레임: {frame.name or 'Main'}, 셀렉터: {selector}")
                            break
                    except:
                        continue
                if target_element:
                    break
            
            if not target_element:
                logger.warning("   ⚠️ 모든 프레임에서 버튼을 찾지 못했습니다. 스크린샷 저장을 시도합니다.")
                try:
                    self.page.screenshot(path="logs/debug_unreflected_filter.png")
                    logger.info("   📸 디버그 스크린샷 저장 완료: logs/debug_unreflected_filter.png")
                except:
                    pass
                return False

            target_element.click(force=True)
            logger.info("   데이터 로딩 대기 (10초)...")
            time.sleep(10)
            return True
        except Exception as e:
            logger.error(f"❌ 미반영 버튼 클릭 실패: {e}")
            return False

    def read_payment_data(self) -> list:
        """결제내역조회 테이블에서 데이터 읽기"""
        logger.info("📊 테이블 데이터 읽기 중...")
        try:
            # 각 컬럼의 모든 셀 가져오기
            date_cells = self.page.locator('span[data-column-id="SETL_REQST_DTM"]').all()
            customer_cells = self.page.locator('span[data-column-id="CUST_NM"]').all()
            amount_cells = self.page.locator('span[data-column-id="SETL_AMT"]').all()
            account_cells = self.page.locator('span[data-column-id="ACQUER_NM"]').all()
            status_cells = self.page.locator('span[data-column-id="SETL_STAT_NM"]').all()

            row_count = len(date_cells)
            logger.info(f"   발견된 행 수: {row_count}")

            if row_count <= 1:
                logger.info("ℹ️ 데이터가 없습니다 (헤더 제외)")
                return []

            data = []
            for i in range(1, row_count):
                try:
                    date_val = date_cells[i].inner_text().strip()
                    # 헤더 행 또는 불필요한 행 필터링
                    if date_val == "결제요청일시" or not date_val:
                        logger.info(f"   ⏩ 행 {i} 건너뜀 (헤더 또는 빈 데이터)")
                        continue

                    data.append({
                        'date_raw': date_val,
                        'customer': customer_cells[i].inner_text().strip() if i < len(customer_cells) else "",
                        'amount': amount_cells[i].inner_text().strip() if i < len(amount_cells) else "",
                        'account': account_cells[i].inner_text().strip() if i < len(account_cells) else "",
                        'status': status_cells[i].inner_text().strip() if i < len(status_cells) else ""
                    })
                except Exception as e:
                    logger.warning(f"   ⚠️ 행 {i} 읽기 오류: {e}")
                    continue

            logger.info(f"✅ {len(data)}건 데이터 읽기 완료")
            return data
        except Exception as e:
            logger.error(f"❌ 데이터 읽기 실패: {e}")
            return []
