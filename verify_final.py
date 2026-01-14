import asyncio
import time
from core.browser import BrowserManager
from core.logger import logger

async def verify():
    # 1. 브라우저 시작 (기존 세션 활용)
    bm = BrowserManager()
    await bm.start(headless=True)
    
    try:
        page = bm.page
        url = "https://loginab.ecount.com/ec5/view/erp?w_flag=1&ec_req_sid=AB-ET3fFoOKSqizx#menuType=MENUTREE_000001&menuSeq=MENUTREE_000016&groupSeq=MENUTREE_000016&prgId=C000016&depth=2"
        
        logger.info(f"🌐 검증 페이지 접속: {url}")
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        logger.info("⏳ 데이터 로딩 대기 (10초)...")
        await asyncio.sleep(10)
        
        # 스크린샷 저장
        screenshot_path = "logs/verify_final_evidence.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"📸 검증 스크린샷 저장 완료: {screenshot_path}")
        
        # '입금보고서' 텍스트 카운트 (간이 검증)
        content = await page.content()
        count = content.count("입금보고서")
        logger.info(f"📊 페이지 내 '입금보고서' 키워드 발견 횟수: {count}")
        
    except Exception as e:
        logger.error(f"❌ 검증 중 오류 발생: {e}")
    finally:
        await bm.stop()

if __name__ == "__main__":
    asyncio.run(verify())
