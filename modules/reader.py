import time
import pandas as pd
from pathlib import Path
from core.logger import logger
from utils.config import PAYMENT_QUERY_HASH


class ReaderModule:
    def __init__(self, page, browser_manager=None):
        self.page = page
        self.browser_manager = browser_manager
        self.grid_selector = 'span[data-column-id="SETL_REQST_DTM"]'

    def _get_erp_target(self):
        if self.browser_manager:
            return self.browser_manager.get_erp_frame()
        return self.page

    def _wait_for_payment_grid(self, timeout=20000):
        target = self._get_erp_target()
        target.wait_for_selector(self.grid_selector, timeout=timeout)
        row_count = target.locator(self.grid_selector).count()
        if row_count == 0:
            raise Exception("결제내역조회 화면 진입 실패 - 그리드 미감지")
        return row_count

    def navigate_to_payment_query(self) -> bool:
        """결제내역조회 페이지로 이동"""
        try:
            logger.info("[NAV] 결제내역조회 페이지로 이동...")
            if self.browser_manager and not self.browser_manager.wait_for_erp_shell(timeout=30000):
                raise Exception("ERP shell is not ready")
            target = self._get_erp_target()

            try:
                target.wait_for_selector('a#link_depth4_MENUTREE_002905', timeout=20000)
                logger.info("   [OK] ERP 셸 안정화 확인")
            except Exception:
                logger.warning("   [WARN] 메뉴 링크 미감지 - 해시 방식으로 진행")

            try:
                target.locator('a#link_depth4_MENUTREE_002905').click()
                logger.info("   [OK] 결제내역조회 메뉴 클릭")
            except Exception:
                js_code = f"window.location.hash = '{PAYMENT_QUERY_HASH}';"
                target.evaluate(js_code)
                logger.warning("   [WARN] 메뉴 클릭 실패 - 해시 방식 fallback")

            for attempt in range(2):
                try:
                    row_count = self._wait_for_payment_grid(timeout=20000)
                    logger.info(f"   [OK] 그리드 로드 확인 ({row_count}개 요소)")
                    return True
                except Exception as e:
                    if attempt == 0:
                        logger.warning(f"   [WARN] 그리드 1차 실패 - 재시도: {e}")
                        time.sleep(3)
                        continue
                    raise Exception("결제조회 페이지 이동 실패")
            return True
        except Exception as e:
            logger.error(f"[ERROR] 페이지 이동 실패: {e}")
            return False

    def click_unreflected_filter(self) -> bool:
        """'미반영' 필터 클릭"""
        try:
            logger.info("[CLICK] '미반영' 버튼 클릭 시도...")
            time.sleep(5)
            logger.info(f"   현재 페이지 URL: {self.page.url}")
            frames = self.page.frames
            logger.info(f"   감지된 프레임 수: {len(frames)}")
            for i, f in enumerate(frames):
                logger.info(f"   - 프레임 {i}: {f.name} ({f.url[:50]}...)")

            selectors = [
                'a#tabUnReflect',
                '#tabUnReflect',
                'text="미반영"',
                '.unreflected',
                'li[id*="tabUnReflect"] a',
            ]

            target_element = None
            for frame in self.page.frames:
                for selector in selectors:
                    try:
                        el = frame.locator(selector).first
                        if el.is_visible(timeout=3000):
                            target_element = el
                            logger.info(
                                f"   [OK] 매칭 발견! 프레임: {frame.name or 'Main'}, 셀렉터: {selector}"
                            )
                            break
                    except Exception:
                        continue
                if target_element:
                    break

            if not target_element:
                logger.warning(
                    "   [WARN] 모든 프레임에서 버튼을 찾지 못했습니다. 스크린샷 저장을 시도합니다."
                )
                try:
                    self.page.screenshot(path="logs/debug_unreflected_filter.png")
                    logger.info(
                        "   [SCREENSHOT] 디버그 스크린샷 저장 완료: logs/debug_unreflected_filter.png"
                    )
                except Exception:
                    pass
                return False

            target_element.click(force=True)
            row_count = self._wait_for_payment_grid(timeout=15000)
            logger.info(f"   [OK] 미반영 그리드 로드 확인 ({row_count}개 요소)")
            return True
        except Exception as e:
            logger.error(f"[ERROR] 미반영 버튼 클릭 실패: {e}")
            return False

    def read_payment_data(self) -> list:
        """결제내역조회 테이블에서 데이터 읽기"""
        logger.info("[READ] 결제내역 데이터 읽기 프로세스 진입...")
        try:
            time.sleep(5)
            target = self._get_erp_target()

            date_cells = target.locator(self.grid_selector).all()
            customer_cells = target.locator('span[data-column-id="CUST_NM"]').all()
            amount_cells = target.locator('span[data-column-id="SETL_AMT"]').all()
            account_cells = target.locator('span[data-column-id="ACQUER_NM"]').all()
            status_cells = target.locator('span[data-column-id="SETL_STATUS_TYPE"]').all()
            auth_no_cells = target.locator('span[data-column-id="APVL_NO"]').all()

            row_count = len(date_cells)
            logger.info(f"   감지된 데이터 행: {row_count}건")

            if row_count == 0:
                raise Exception("결제내역조회 화면 진입 실패 - 그리드 미감지")

            if row_count <= 1:
                logger.info("[INFO] 현재 미반영 데이터가 없거나 로딩되지 않았습니다.")
                return []

            data = []
            for i in range(1, row_count):
                try:
                    date_val = date_cells[i].inner_text().strip()
                    if "결제요청" in date_val or not date_val:
                        continue

                    auth_no = ""
                    if i < len(auth_no_cells):
                        auth_no = auth_no_cells[i].inner_text().strip()
                        if auth_no == "승인번호":
                            auth_no = ""

                    data.append({
                        'date_raw': date_val,
                        'customer': customer_cells[i].inner_text().strip() if i < len(customer_cells) else "",
                        'amount': amount_cells[i].inner_text().strip() if i < len(amount_cells) else "",
                        'account': account_cells[i].inner_text().strip() if i < len(account_cells) else "",
                        'status': status_cells[i].inner_text().strip() if i < len(status_cells) else "",
                        'auth_no': auth_no,
                    })
                except Exception as e:
                    logger.warning(f"   [WARN] 행 {i} 읽기 오류: {e}")
                    continue

            logger.info(f"[OK] 총 {len(data)}건의 유효 데이터 추출 완료")
            return data
        except Exception as e:
            logger.error(f"[ERROR] 데이터 읽기 실패: {e}")
            return []

    def _page_signature(self, rows: list) -> tuple:
        """Small signature used to detect whether pagination actually moved."""
        if not rows:
            return ("empty",)
        head = tuple(row.get("date_raw", "") for row in rows[:5])
        tail = tuple(row.get("date_raw", "") for row in rows[-2:])
        return (len(rows),) + head + tail

    def _current_grid_signature(self) -> tuple:
        """Read a cheap DOM-only signature for the currently visible payment grid."""
        target = self._get_erp_target()
        values = target.evaluate(
            """
            () => Array.from(document.querySelectorAll('span[data-column-id="SETL_REQST_DTM"]'))
                .map((el) => el.innerText.trim())
                .filter(Boolean)
                .slice(1)
            """
        )
        if not values:
            return ("empty",)
        return (len(values),) + tuple(values[:5]) + tuple(values[-2:])

    def _click_page_number(self, page_no: int, previous_signature: tuple = None) -> bool:
        """Move to a grid page and verify that the visible grid actually changed."""
        target = self._get_erp_target()
        strategies = [
            ("number", "number"),
            ("input", "input"),
            ("next", "next"),
        ]

        for label, mode in strategies:
            moved = target.evaluate(
                """
                ({ pageNo, mode }) => {
                    const wanted = String(pageNo);
                    const firstGridCell = document.querySelector('span[data-column-id="SETL_REQST_DTM"]');
                    const gridTop = firstGridCell ? firstGridCell.getBoundingClientRect().top : null;
                    const isVisible = (el) => {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none';
                    };
                    const isPagerArea = (el) => {
                        if (gridTop === null) {
                            return true;
                        }
                        const rect = el.getBoundingClientRect();
                        return rect.bottom <= gridTop + 5;
                    };
                    const fireClick = (el) => {
                        const target = el.querySelector('a, button, [role="button"]') || el;
                        target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
                        target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
                        target.click();
                    };

                    if (mode === 'number') {
                        const candidates = Array.from(
                            document.querySelectorAll('a, button, [role="button"], li, span')
                        ).filter((el) => (
                            isVisible(el) &&
                            isPagerArea(el) &&
                            el.innerText.trim() === wanted
                        ));
                        if (!candidates.length) {
                            return false;
                        }
                        fireClick(candidates[0]);
                        return true;
                    }

                    if (mode === 'input') {
                        const inputs = Array.from(document.querySelectorAll('input'))
                            .filter((el) => {
                                const rect = el.getBoundingClientRect();
                                return isVisible(el) &&
                                    isPagerArea(el) &&
                                    rect.width <= 90 &&
                                    /^\\d+$/.test((el.value || '').trim());
                            });
                        if (!inputs.length) {
                            return false;
                        }
                        const input = inputs[inputs.length - 1];
                        input.focus();
                        input.value = wanted;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        input.dispatchEvent(new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true,
                        }));
                        input.dispatchEvent(new KeyboardEvent('keyup', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true,
                        }));
                        input.blur();
                        return true;
                    }

                    const nextTexts = new Set(['>', '>>', '»', '다음', 'Next']);
                    const nextCandidates = Array.from(
                        document.querySelectorAll('a, button, [role="button"], li, span')
                    ).filter((el) => (
                        isVisible(el) &&
                        isPagerArea(el) &&
                        nextTexts.has(el.innerText.trim())
                    ));
                    if (!nextCandidates.length) {
                        return false;
                    }
                    fireClick(nextCandidates[0]);
                    return true;
                }
                """,
                {"pageNo": page_no, "mode": mode},
            )

            if not moved:
                continue

            logger.info(f"[PAGE] attempted payment page {page_no} via {label}")
            time.sleep(4)
            self._wait_for_payment_grid(timeout=15000)

            if previous_signature is None:
                logger.info(f"[PAGE] moved to payment page {page_no}")
                return True

            new_signature = self._current_grid_signature()
            if new_signature != previous_signature:
                logger.info(f"[PAGE] moved to payment page {page_no}")
                return True

            logger.warning(f"[PAGE] payment page {page_no} via {label} did not change grid")

        logger.info(f"[PAGE] no working payment page {page_no} control")
        return False

    def read_all_payment_pages(self, max_pages: int = 10) -> list:
        """Read the current unreflected grid page and following pagination pages."""
        all_rows = []
        seen_signatures = set()

        for page_no in range(1, max_pages + 1):
            rows = self.read_payment_data()
            signature = self._page_signature(rows)

            if signature in seen_signatures:
                logger.warning(f"[PAGE] duplicate page signature at page {page_no}; stopping pagination")
                break

            seen_signatures.add(signature)
            all_rows.extend(rows)
            logger.info(f"[PAGE] page {page_no} collected {len(rows)} rows (total {len(all_rows)})")

            if not self._click_page_number(page_no + 1, signature):
                break

        logger.info(f"[PAGE] collected {len(all_rows)} rows across {len(seen_signatures)} page(s)")
        return all_rows

    def get_reflected_status(self) -> set:
        """'회계반영' 탭에서 이미 처리된 승인번호 목록 수집"""
        logger.info("[CHECK] 실시간 '회계반영' 내역 확인 중...")
        try:
            time.sleep(8)

            selectors = ['a#tabReflect', 'text="회계반영"', '#tabReflect', '.reflected']
            btn_found = False
            target_frame = None
            for frame in self.page.frames:
                for sel in selectors:
                    try:
                        el = frame.locator(sel).first
                        if el.is_visible(timeout=3000):
                            el.click(force=True)
                            btn_found = True
                            target_frame = frame
                            break
                    except Exception:
                        continue
                if btn_found:
                    break

            if not btn_found:
                logger.warning("   [WARN] '회계반영' 버튼을 찾지 못해 실시간 체크를 건너뜁니다.")
                return set()

            time.sleep(5)

            reflected_nos = set()
            source = target_frame or self._get_erp_target()
            no_cells = source.locator('span[data-column-id="APVL_NO"]').all()

            for cell in no_cells:
                text = cell.inner_text().strip()
                if text and text != "승인번호":
                    reflected_nos.add(text)

            logger.info(f"   [OK] 실시간 회계반영 {len(reflected_nos)}건 감지")

            self.click_unreflected_filter()
            return reflected_nos

        except Exception as e:
            logger.error(f"[ERROR] 실시간 내역 수집 실패: {e}")
            return set()
