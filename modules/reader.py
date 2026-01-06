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
            time.sleep(15) # 로딩 시간 증대 (네트워크 지연 대비)
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
        logger.info("📊 결제내역 데이터 읽기 프로세스 진입...")
        try:
            # 데이터 로딩 시간 확보
            time.sleep(5)
            
            # 각 컬럼의 모든 셀 가져오기
            date_cells = self.page.locator('span[data-column-id="SETL_REQST_DTM"]').all()
            customer_cells = self.page.locator('span[data-column-id="CUST_NM"]').all()
            amount_cells = self.page.locator('span[data-column-id="SETL_AMT"]').all()
            account_cells = self.page.locator('span[data-column-id="ACQUER_NM"]').all()
            status_cells = self.page.locator('span[data-column-id="SETL_STAT_NM"]').all()
            auth_no_cells = self.page.locator('span[data-column-id="APVL_NO"]').all() 

            row_count = len(date_cells)
            logger.info(f"   감지된 데이터 행: {row_count}건")

            if row_count <= 1:
                logger.info("ℹ️ 현재 미반영 데이터가 없거나 로딩되지 않았습니다.")
                return []

            data = []
            for i in range(1, row_count):
                try:
                    date_val = date_cells[i].inner_text().strip()
                    if "결제요청" in date_val or not date_val:
                        continue

                    # 승인번호 (안전하게 인덱스 확인)
                    auth_no = ""
                    if i < len(auth_no_cells):
                        auth_no = auth_no_cells[i].inner_text().strip()
                        if auth_no == "승인번호": auth_no = ""

                    data.append({
                        'date_raw': date_val,
                        'customer': customer_cells[i].inner_text().strip() if i < len(customer_cells) else "",
                        'amount': amount_cells[i].inner_text().strip() if i < len(amount_cells) else "",
                        'account': account_cells[i].inner_text().strip() if i < len(account_cells) else "",
                        'status': status_cells[i].inner_text().strip() if i < len(status_cells) else "",
                        'auth_no': auth_no
                    })
                except Exception as e:
                    logger.warning(f"   ⚠️ 행 {i} 읽기 오류: {e}")
                    continue

            logger.info(f"✅ 총 {len(data)}건의 유효 데이터 추출 완료")
            return data
        except Exception as e:
            logger.error(f"❌ 데이터 읽기 실패: {e}")
            return []
    def get_reflected_status(self) -> set:
        """'회계반영' 탭에서 이미 처리된 승인번호 목록 수집 (실시간 중복 체크용)"""
        logger.info("🔍 실시간 '회계반영' 내역 확인 중...")
        try:
            # 탭 로딩 대기 강화
            time.sleep(8)
            
            # 1. '회계반영' 버튼 클릭
            selectors = ['a#tabReflect', 'text="회계반영"', '#tabReflect', '.reflected']
            btn_found = False
            for frame in self.page.frames:
                for sel in selectors:
                    try:
                        el = frame.locator(sel).first
                        if el.is_visible(timeout=3000):
                            el.click(force=True)
                            btn_found = True
                            break
                    except: continue
                if btn_found: break
            
            if not btn_found:
                logger.warning("   ⚠️ '회계반영' 버튼을 찾지 못해 실시간 체크를 건너뜁니다.")
                return set()

            time.sleep(5) # 로딩 대기
            
            # 2. 승인번호 컬럼(APVL_NO) 데이터 수집
            reflected_nos = set()
            no_cells = self.page.locator('span[data-column-id="APVL_NO"]').all()
            
            for cell in no_cells:
                text = cell.inner_text().strip()
                if text and text != "승인번호":
                    reflected_nos.add(text)
            
            logger.info(f"   ✅ 실시간 회계반영 {len(reflected_nos)}건 감지됨")
            
            # 다시 '미반영' 탭으로 복구 (다음 작업을 위해)
            self.click_unreflected_filter()
            
            return reflected_nos
            
        except Exception as e:
            logger.error(f"❌ 실시간 내역 수집 실패: {e}")
            return set()
