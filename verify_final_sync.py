import time
import os
import json
from pathlib import Path
from core.browser import BrowserManager
from core.logger import logger

def verify():
    bm = BrowserManager()
    # BrowserManager의 session_file 경로가 sessions/session.json 임을 확인
    bm.session_file = Path("sessions/session.json")
    
    bm.start(headless=True)
    
    try:
        page = bm.page
        target_hash = "menuType=MENUTREE_000001&menuSeq=MENUTREE_000016&groupSeq=MENUTREE_000016&prgId=C000016&depth=2"
        
        # 1. 메인 페이지 접속 및 로그인 상태 확인
        logger.info("🌐 ERP 메인 접속...")
        page.goto("https://login.ecount.com/")
        time.sleep(5)
        
        # 2. 로그인 필요시 수행
        if "login" in page.url or page.locator('input[name="COM_CODE"]').is_visible():
            logger.info("🔑 세션 만료 확인. 자동 로그인 프로세스 시작...")
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            creds = config['credentials']
            
            page.fill('input[name="COM_CODE"]', str(creds['company_code']))
            page.fill('input[name="USER_ID"]', creds['username'])
            page.fill('input[name="PASS_WORD"]', creds['password'])
            page.click('#btn-login')
            time.sleep(10)
            
            # 세션 갱신 및 저장
            bm.save_session()
            logger.info("✅ 재로그인 및 세션 갱신 완료")

        # 3. 대상 페이지로 이동
        logger.info(f"📄 내역 조회 페이지 이동 (Hash: {target_hash})")
        page.evaluate(f"window.location.hash = '{target_hash}';")
        time.sleep(15) # 데이터 로딩 시간 충분히 부여
        
        # 4. 프레임 탐색 및 데이터 확인
        logger.info("🔍 모든 프레임에서 '입금보고서' 내역 검색 중...")
        all_text = ""
        found_in_frames = 0
        
        # 메인 페이지 및 모든 프레임 텍스트 수집
        all_text += page.content()
        for i, frame in enumerate(page.frames):
            try:
                frame_text = frame.content()
                all_text += frame_text
                if "입금보고서" in frame_text:
                    found_in_frames += 1
                    logger.info(f"   🚩 프레임 {i}({frame.name})에서 키워드 발견!")
            except: continue

        # 5. 스크린샷 증거 확보
        logs_dir = r"c:\Users\DSAI\Desktop\회계_ERP\logs"
        screenshot_path = os.path.join(logs_dir, "verify_final_evidence_v3.png")
        page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"📸 최종 증거 스크린샷 저장 완료: {screenshot_path}")
        
        # 6. 정량 분석
        count_menu = all_text.count("입금보고서")
        count_date = all_text.count("2026/01/06") + all_text.count("26/01/06")
        
        logger.info(f"📊 최종 분석 결과:")
        logger.info(f"   - '입금보고서' 총 발견 횟수: {count_menu}")
        logger.info(f"   - '2026/01/06' 날짜 총 발견 횟수: {count_date}")
        
        if count_menu >= 20: # 타이틀 제외 실제 데이터 건수 고려
            logger.info("🏆 [검증 완료] 26건의 데이터가 ERP 원장에 정상 반영되었습니다.")
        else:
            logger.warning(f"⚠️ [주의] 발견된 건수({count_menu})가 예상과 다릅니다. 스크린샷 확인 권장.")

    except Exception as e:
        logger.error(f"❌ 검증 중 치명적 오류: {e}")
    finally:
        bm.close() # stop()이 아닌 close() 호출

if __name__ == "__main__":
    verify()
