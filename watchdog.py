#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automation watchdog
- Monitors heartbeat freshness
- Restarts automation when heartbeat is stale/missing
"""

import os
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

HEARTBEAT_FILE = Path("heartbeat.txt")
LOCK_FILE = Path("runtime.lock")
WATCHDOG_LOG_DIR = Path("logs")
CHECK_INTERVAL = 120
TIMEOUT_MINUTES = 45


def log_event(level: str, message: str):
    now = datetime.now()
    line = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}"
    print(line)
    try:
        WATCHDOG_LOG_DIR.mkdir(exist_ok=True)
        logfile = WATCHDOG_LOG_DIR / f"watchdog_events_{now.strftime('%Y%m%d')}.log"
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] [WARN] watchdog log write failed: {e}")


def check_heartbeat():
    if not HEARTBEAT_FILE.exists():
        return None, "heartbeat.txt not found"

    try:
        last_modified = datetime.fromtimestamp(HEARTBEAT_FILE.stat().st_mtime)
        time_diff = datetime.now() - last_modified
        with open(HEARTBEAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        return time_diff, content
    except Exception as e:
        return None, f"heartbeat read error: {e}"


def cleanup_stale_lock():
    if not LOCK_FILE.exists():
        return

    try:
        pid_text = LOCK_FILE.read_text(encoding="utf-8").strip()
        if not pid_text.isdigit():
            LOCK_FILE.unlink(missing_ok=True)
            log_event("WARN", "Removed invalid runtime.lock")
            return

        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {int(pid_text)}"],
            capture_output=True,
            text=True,
        )
        if pid_text not in result.stdout:
            LOCK_FILE.unlink(missing_ok=True)
            log_event("WARN", f"Removed stale runtime.lock (PID: {pid_text})")
    except Exception as e:
        log_event("ERROR", f"runtime.lock cleanup error: {e}")


def kill_and_restart(reason: str, heartbeat_age_seconds: float | None = None):
    details = f"reason={reason}"
    if heartbeat_age_seconds is not None:
        details += f", heartbeat_age={heartbeat_age_seconds:.0f}s"
    log_event("ALERT", f"Restart requested ({details})")
    try:
        py_kill = subprocess.run(
            ["taskkill", "/F", "/IM", "pythonw.exe", "/T"], capture_output=True, text=True
        )
        ch_kill = subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True, text=True
        )
        log_event("INFO", f"taskkill pythonw rc={py_kill.returncode}")
        log_event("INFO", f"taskkill chrome rc={ch_kill.returncode}")

        cleanup_stale_lock()
        time.sleep(5)

        subprocess.Popen(["pythonw", "main.py"], creationflags=subprocess.CREATE_NO_WINDOW)
        log_event("OK", "Restarted pythonw main.py")
        return True
    except Exception as e:
        log_event("ERROR", f"Restart failed: {e}")
        return False


def main():
    log_event("INFO", "=" * 70)
    log_event("INFO", "Watchdog started")
    log_event("INFO", f"check interval: {CHECK_INTERVAL}s")
    log_event("INFO", f"stale timeout: {TIMEOUT_MINUTES}m")
    log_event("INFO", "=" * 70)

    consecutive_errors = 0

    while True:
        try:
            time_diff, content = check_heartbeat()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if time_diff is None:
                log_event("ERROR", content)
                consecutive_errors += 1

                if consecutive_errors >= 3:
                    log_event("ALERT", f"Consecutive heartbeat errors: {consecutive_errors}")
                    if kill_and_restart("heartbeat_missing", None):
                        consecutive_errors = 0
                        time.sleep(60)
            else:
                consecutive_errors = 0

                if time_diff > timedelta(minutes=TIMEOUT_MINUTES):
                    age = time_diff.total_seconds()
                    log_event("ALERT", f"Heartbeat stale: {age/60:.1f}m")
                    log_event("INFO", f"Heartbeat snapshot: {content.strip().replace(chr(10), ' | ')}")
                    if kill_and_restart("heartbeat_stale", age):
                        time.sleep(60)
                else:
                    log_event("OK", f"heartbeat age: {time_diff.total_seconds():.0f}s")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log_event("INFO", "Watchdog stopped")
            break
        except Exception as e:
            log_event("ERROR", f"loop error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
