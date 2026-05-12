import time
from core.logger import logger

PG_SALES_QUERY_HASH = (
    "menuType=MENUTREE_000001&menuSeq=MENUTREE_002566&"
    "groupSeq=MENUTREE_002562&prgId=E010207&depth=3"
)


class PGReaderModule:
    def __init__(self, page):
        self.page = page

    def navigate_to_pg_sales_query(self) -> bool:
        """결제대행사매출조회 페이지로 이동"""
        try:
            logger.info("[PG][NAV] 결제대행사매출조회 페이지로 이동...")
            js_code = f"window.location.hash = '{PG_SALES_QUERY_HASH}';"
            self.page.evaluate(js_code)
            time.sleep(10)
            return True
        except Exception as e:
            logger.error(f"[PG][ERROR] 페이지 이동 실패: {e}")
            return False

    def _find_visible_locator(self, selectors: list, timeout: int = 3000):
        """현재 페이지와 모든 프레임에서 보이는 요소 탐색"""
        for frame in self.page.frames:
            for selector in selectors:
                try:
                    locator = frame.locator(selector).first
                    if locator.is_visible(timeout=timeout):
                        logger.info(
                            f"[PG][OK] 요소 발견 - 프레임: {frame.name or 'Main'}, 셀렉터: {selector}"
                        )
                        return locator
                except Exception:
                    continue
        return None

    def click_instant_search(self) -> bool:
        """즉시조회 버튼 클릭"""
        try:
            logger.info("[PG][CLICK] 즉시조회 버튼 클릭 시도...")
            time.sleep(3)

            selectors = [
                "button#PGSearch",
                "#PGSearch",
                'button:has-text("즉시조회")',
                'a:has-text("즉시조회")',
            ]
            target = self._find_visible_locator(selectors)
            if not target:
                logger.warning("[PG][WARN] 즉시조회 버튼을 찾지 못했습니다.")
                return False

            target.click(force=True)
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"[PG][ERROR] 즉시조회 클릭 실패: {e}")
            return False

    def click_popup_search(self) -> bool:
        """첫 번째 팝업에서 조회 링크 클릭"""
        try:
            logger.info("[PG][CLICK] 첫 번째 팝업에서 조회 클릭 시도...")
            selectors = [
                'a:has-text("조회")',
                'button:has-text("조회")',
                'span:has-text("조회")',
            ]
            target = self._find_visible_locator(selectors)
            if not target:
                logger.warning("[PG][WARN] 팝업의 조회 버튼을 찾지 못했습니다.")
                return False

            target.click(force=True)
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"[PG][ERROR] 팝업 조회 클릭 실패: {e}")
            return False

    def click_popup_apply(self) -> bool:
        """두 번째 팝업에서 적용 버튼 클릭"""
        try:
            logger.info("[PG][CLICK] 두 번째 팝업에서 적용 클릭 시도...")
            selectors = [
                "button#apply",
                "#apply",
                'button:has-text("적용")',
                'a:has-text("적용")',
            ]
            target = self._find_visible_locator(selectors)
            if not target:
                logger.warning("[PG][WARN] 적용 버튼을 찾지 못했습니다.")
                return False

            target.click(force=True)
            time.sleep(8)
            return True
        except Exception as e:
            logger.error(f"[PG][ERROR] 적용 클릭 실패: {e}")
            return False

    def read_pg_sales_data(self) -> list:
        """결제대행사매출조회 결과 데이터 읽기"""
        logger.info("[PG][READ] 결제대행사매출조회 데이터 읽기 시작...")
        try:
            time.sleep(5)

            date_cells = self.page.locator('span[data-column-id="SETL_DT"]').all()
            status_cells = self.page.locator('span[data-column-id="APV_TYPE_CD"]').all()
            customer_cells = self.page.locator('span[data-column-id="RCPTR_NM"]').all()
            amount_cells = self.page.locator('span[data-column-id="TAMT"]').all()
            account_cells = self.page.locator('span[data-column-id="PGCO_ALNM"]').all()

            row_count = len(date_cells)
            logger.info(f"[PG][INFO] 감지된 데이터 행: {row_count}건")

            if row_count <= 1:
                logger.info("[PG][INFO] 조회 결과가 없거나 로딩되지 않았습니다.")
                return []

            data = []
            for i in range(1, row_count):
                try:
                    date_val = date_cells[i].inner_text().strip()
                    if not date_val or date_val == "일자":
                        continue

                    status = status_cells[i].inner_text().strip() if i < len(status_cells) else ""
                    customer = customer_cells[i].inner_text().strip() if i < len(customer_cells) else ""
                    amount = amount_cells[i].inner_text().strip() if i < len(amount_cells) else ""
                    account = account_cells[i].inner_text().strip() if i < len(account_cells) else ""

                    data.append(
                        {
                            "date_raw": date_val,
                            "customer": customer,
                            "amount": amount,
                            "account": account,
                            "status": status,
                        }
                    )
                except Exception as e:
                    logger.warning(f"[PG][WARN] 행 {i} 읽기 오류: {e}")
                    continue

            logger.info(f"[PG][OK] 총 {len(data)}건의 유효 데이터 추출 완료")
            return data
        except Exception as e:
            logger.error(f"[PG][ERROR] 데이터 읽기 실패: {e}")
            return []
