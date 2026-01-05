import json
from pathlib import Path

def load_config():
    """설정 파일 로드"""
    # 프로젝트 루트의 config.json 탐색
    config_file = Path(__file__).parent.parent / "config.json"
    if not config_file.exists():
        # 없으면 예시 파일 참고
        config_file = Path(__file__).parent.parent / "config.example.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

config = load_config()

# 주요 설정값 상수화
MODE = config.get("mode", "test")  # 'test' or 'production'

CREDENTIALS = config.get("credentials", {})
URLS = config.get("urls", {})

# URL 상세
LOGIN_URL = URLS.get("login", "https://login.ecount.com/")
PAYMENT_QUERY_HASH = URLS.get("payment_query_hash", "menuType=MENUTREE_000004&menuSeq=MENUTREE_002905&groupSeq=MENUTREE_000030&prgId=E040254&depth=4")
DEPOSIT_REPORT_HASH = URLS.get("deposit_report_hash", "menuType=MENUTREE_000001&menuSeq=MENUTREE_000069&groupSeq=MENUTREE_000010&prgId=E010403&depth=3")

# 모드별 설정
BROWSER_CONFIG = config.get("browser", {})
SCHEDULE_CONFIG = config.get("schedule", {})
NOTIFICATION_CONFIG = config.get("notification", {})

# 레거시 호환 및 간축 변수
# mode가 'production'인 경우에만 headless를 기본값으로 하거나 명시적 설정 따름
TEST_MODE = (MODE == "test")
HEADLESS_MODE = BROWSER_CONFIG.get("headless", False if TEST_MODE else True)
TIMEOUT = BROWSER_CONFIG.get("timeout", 30000)
