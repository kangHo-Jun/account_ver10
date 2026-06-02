#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERP 자동화 상태 진단 도구
실행: python health_check.py
"""

import io
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Windows cp949 콘솔에서 한글 출력 보장
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LOCK_FILE = Path("runtime.lock")
WATCHDOG_LOCK_FILE = Path("watchdog.lock")
HEARTBEAT_FILE = Path("heartbeat.txt")
LOGS_DIR = Path("logs")


def is_process_running(pid: int) -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True,
        )
        return str(pid) in result.stdout
    except Exception:
        return False


def check_process(lock_file: Path) -> tuple[str, str]:
    if not lock_file.exists():
        return "미실행", "[ -- ]"
    try:
        pid_text = lock_file.read_text(encoding="utf-8").strip()
        if not pid_text.isdigit():
            return "락 파일 손상", "[WARN]"
        pid = int(pid_text)
        if is_process_running(pid):
            return f"실행 중 (PID {pid})", "[ OK ]"
        return f"락 파일 있음 - PID {pid} 종료됨", "[WARN]"
    except Exception as e:
        return f"확인 실패: {e}", "[ERR ]"


def check_heartbeat() -> tuple[str, str]:
    if not HEARTBEAT_FILE.exists():
        return "파일 없음", "[ERR ]"
    try:
        last_modified = datetime.fromtimestamp(HEARTBEAT_FILE.stat().st_mtime)
        age_min = (datetime.now() - last_modified).total_seconds() / 60
        time_str = last_modified.strftime("%H:%M:%S")
        label = f"{age_min:.0f}분 전 ({time_str})"
        if age_min < 35:
            return label, "[ OK ]"
        if age_min < 50:
            return label, "[WARN]"
        return label, "[ERR ]"
    except Exception as e:
        return f"확인 실패: {e}", "[ERR ]"


def check_latest_log() -> tuple[str, str]:
    try:
        logs = sorted(LOGS_DIR.glob("v9_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            return "로그 없음", "[WARN]"
        latest = logs[0]
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)
        return f"{latest.name} ({mtime.strftime('%H:%M')})", "[ OK ]"
    except Exception as e:
        return f"확인 실패: {e}", "[ERR ]"


def check_latest_upload() -> str:
    try:
        logs = sorted(LOGS_DIR.glob("v9_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            return "없음"
        with open(logs[0], "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            m = re.search(r"저장 성공 확정.*?(\d+)건", line)
            if m:
                ts = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", line)
                time_str = ts.group(1) if ts else ""
                return f"OUT {m.group(1)}건 ({time_str})"
        return "업로드 기록 없음"
    except Exception as e:
        return f"확인 실패: {e}"


def main():
    main_status, main_flag = check_process(LOCK_FILE)
    wdog_status, wdog_flag = check_process(WATCHDOG_LOCK_FILE)
    hb_status, hb_flag = check_heartbeat()
    log_status, log_flag = check_latest_log()
    upload_status = check_latest_upload()

    flags = [main_flag, wdog_flag, hb_flag, log_flag]
    if "[ERR ]" in flags:
        verdict = "[ERR ] 이상 감지 - 즉시 확인 필요"
    elif "[WARN]" in flags:
        verdict = "[WARN] 주의 필요"
    elif "[ -- ]" in flags:
        verdict = "[ -- ] 일부 프로세스 미실행"
    else:
        verdict = "[ OK ] 정상"

    sep = "=" * 42
    print(sep)
    print("    ERP 자동화 상태 진단")
    print(sep)
    print(f"  메인 프로세스  : {main_flag}  {main_status}")
    print(f"  워치독        : {wdog_flag}  {wdog_status}")
    print(f"  Heartbeat 나이: {hb_flag}  {hb_status}")
    print(f"  최근 로그     :        {log_status}")
    print(f"  최근 업로드   :        {upload_status}")
    print(sep)
    print(f"  판정          : {verdict}")
    print(sep)


if __name__ == "__main__":
    main()
