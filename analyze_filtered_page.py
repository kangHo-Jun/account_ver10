"""
필터링된 페이지 구조 분석 스크립트
- 결제내역조회 페이지에서 '승인/취소' 필터 적용 방법 확인
- 데이터 컬럼 구조 확인
- 기존 세션 활용
"""

import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.config import PAYMENT_QUERY_HASH

def analyze_page():
    print("[시작] 필터링 페이지 분석...")

    # 세션 파일 로드
    session_file = Path("sessions/session.json")
    if not session_file.exists():
        print("[오류] 세션 파일이 없습니다. 메인 프로그램이 실행 중인지 확인하세요.")
        return

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # 세션 쿠키 로드
        print("[1] 기존 세션 쿠키 로드...")
        cookies = session_data.get('cookies', [])
        if cookies:
            context.add_cookies(cookies)
            print(f"    쿠키 {len(cookies)}개 로드 완료")

        page = context.new_page()

        # 저장된 URL로 이동
        saved_url = session_data.get('url', '')
        print(f"[2] 저장된 URL로 이동: {saved_url[:60]}...")
        page.goto(saved_url)
        time.sleep(5)

        # 2. 결제내역조회 페이지로 이동
        print(f"[3] 결제내역조회 페이지 이동...")
        print(f"    Hash: {PAYMENT_QUERY_HASH}")
        js_code = f"window.location.hash = '{PAYMENT_QUERY_HASH}';"
        page.evaluate(js_code)
        time.sleep(10)

        # 3. 현재 페이지 URL 확인
        print(f"[4] 현재 URL: {page.url}")

        # 4. 페이지 구조 분석 - 탭/필터 버튼 찾기
        print("\n[5] 페이지 탭/필터 버튼 분석...")

        # 모든 탭 요소 찾기
        for frame in page.frames:
            print(f"\n--- 프레임: {frame.name or 'Main'} ---")

            # 탭 버튼들 찾기
            tabs = frame.query_selector_all('a[id^="tab"], li[class*="tab"], div[class*="tab"]')
            for tab in tabs[:10]:  # 상위 10개만
                try:
                    text = tab.inner_text().strip()[:30]
                    tab_id = tab.get_attribute('id') or ''
                    print(f"  탭: [{tab_id}] {text}")
                except:
                    pass

            # 셀렉트박스 (필터) 찾기
            selects = frame.query_selector_all('select')
            for sel in selects[:5]:
                try:
                    sel_id = sel.get_attribute('id') or sel.get_attribute('name') or ''
                    options = sel.query_selector_all('option')
                    opt_texts = [o.inner_text().strip()[:20] for o in options[:5]]
                    print(f"  셀렉트: [{sel_id}] 옵션: {opt_texts}")
                except:
                    pass

            # 결제상태 필터 관련 요소 찾기
            status_elements = frame.query_selector_all('[class*="status"], [id*="status"], [name*="status"], [id*="STAT"], [name*="STAT"]')
            for el in status_elements[:5]:
                try:
                    el_id = el.get_attribute('id') or el.get_attribute('name') or ''
                    print(f"  상태필터: [{el_id}]")
                except:
                    pass

        # 5. 현재 테이블 데이터 구조 확인
        print("\n[6] 테이블 데이터 컬럼 확인...")
        status_cells = page.locator('span[data-column-id="SETL_STAT_NM"]').all()
        print(f"   결제상태(SETL_STAT_NM) 셀 개수: {len(status_cells)}")

        # 첫 10개 상태값 출력
        statuses = []
        for i, cell in enumerate(status_cells[:10]):
            try:
                text = cell.inner_text().strip()
                statuses.append(text)
            except:
                pass
        print(f"   상태 샘플: {statuses}")

        # 6. 스크린샷 저장
        print("\n[7] 스크린샷 저장...")
        page.screenshot(path="logs/analyze_filtered_page.png", full_page=True)
        print("   저장 완료: logs/analyze_filtered_page.png")

        # 7. 수동 확인을 위해 대기
        print("\n[8] 브라우저를 열어둡니다. 직접 확인 후 Enter 키를 누르세요...")
        input(">>> Enter 키로 종료: ")

        browser.close()
        print("\n[완료] 분석 종료")

if __name__ == "__main__":
    analyze_page()
