#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automation watchdog
- Singleton via watchdog.lock (prevents duplicate watchdog instances)
- Monitors heartbeat freshness
- Restarts automation when heartbeat is stale/missing
- Sends email alert + local ALERT file on restart
- Retries once (60s later) if first restart does not recover heartbeat
"""

import os
import json
import time
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta

HEARTBEAT_FILE = Path("heartbeat.txt")
LOCK_FILE = Path("runtime.lock")
WATCHDOG_LOCK_FILE = Path("watchdog.lock")
WATCHDOG_LOG_DIR = Path("logs")
CHECK_INTERVAL = 120
TIMEOUT_MINUTES = 45


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Process helpers
# ---------------------------------------------------------------------------

def is_process_running(pid: int) -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True,
        )
        return str(pid) in result.stdout
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Watchdog singleton lock
# ---------------------------------------------------------------------------

def acquire_watchdog_lock() -> bool:
    """Ensure only one watchdog instance runs. Returns False if another is live."""
    if WATCHDOG_LOCK_FILE.exists():
        try:
            pid_text = WATCHDOG_LOCK_FILE.read_text(encoding="utf-8").strip()
            if pid_text.isdigit() and is_process_running(int(pid_text)):
                log_event("WARN", f"Another watchdog already running (PID: {pid_text}). Exiting.")
                return False
            # Stale lock — clean up
            WATCHDOG_LOCK_FILE.unlink(missing_ok=True)
            log_event("WARN", f"Removed stale watchdog.lock (PID: {pid_text})")
        except Exception as e:
            log_event("WARN", f"watchdog.lock read error: {e}. Overwriting.")

    try:
        WATCHDOG_LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
        log_event("INFO", f"WATCHDOG_START pid={os.getpid()} timeout={TIMEOUT_MINUTES}m interval={CHECK_INTERVAL}s")
        return True
    except Exception as e:
        log_event("ERROR", f"Failed to write watchdog.lock: {e}")
        return False


def release_watchdog_lock():
    try:
        WATCHDOG_LOCK_FILE.unlink(missing_ok=True)
        log_event("INFO", "Watchdog lock released")
    except Exception as e:
        log_event("WARN", f"Failed to release watchdog.lock: {e}")


# ---------------------------------------------------------------------------
# Alert (email + local file fallback)
# ---------------------------------------------------------------------------

def _load_email_config() -> dict:
    try:
        cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
        return cfg.get("notification", {}).get("email", {})
    except Exception:
        return {}


def send_alert(subject: str, body: str):
    """Send email alert; fall back to a local ALERT_*.txt file if email fails."""
    cfg = _load_email_config()
    sent = False

    if cfg.get("enabled"):
        sender = cfg.get("sender", "")
        password = cfg.get("sender_password", "")
        recipient = cfg.get("recipient", "")
        if all([sender, password, recipient]):
            try:
                msg = MIMEMultipart()
                msg["From"] = sender
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))
                with smtplib.SMTP(cfg.get("smtp_server", "smtp.gmail.com"),
                                   cfg.get("smtp_port", 587)) as s:
                    s.starttls()
                    s.login(sender, password)
                    s.sendmail(sender, recipient, msg.as_string())
                log_event("OK", f"Alert email sent: {subject}")
                sent = True
            except Exception as e:
                log_event("WARN", f"Alert email failed: {e}")

    if not sent:
        try:
            WATCHDOG_LOG_DIR.mkdir(exist_ok=True)
            alert_path = WATCHDOG_LOG_DIR / f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            alert_path.write_text(f"{subject}\n\n{body}", encoding="utf-8")
            log_event("INFO", f"Local alert file written: {alert_path.name}")
        except Exception as e:
            log_event("WARN", f"Local alert file write failed: {e}")


# ---------------------------------------------------------------------------
# Heartbeat check
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Lock cleanup + restart
# ---------------------------------------------------------------------------

def cleanup_stale_lock():
    if not LOCK_FILE.exists():
        return
    try:
        pid_text = LOCK_FILE.read_text(encoding="utf-8").strip()
        if not pid_text.isdigit():
            LOCK_FILE.unlink(missing_ok=True)
            log_event("WARN", "Removed invalid runtime.lock")
            return
        if not is_process_running(int(pid_text)):
            LOCK_FILE.unlink(missing_ok=True)
            log_event("WARN", f"Removed stale runtime.lock (PID: {pid_text})")
    except Exception as e:
        log_event("ERROR", f"runtime.lock cleanup error: {e}")


def kill_and_restart(reason: str, heartbeat_age_seconds: float | None, attempt: int = 1) -> bool:
    age_min = heartbeat_age_seconds / 60 if heartbeat_age_seconds is not None else 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_event("ALERT", f"HEARTBEAT_STALE age={age_min:.1f}m -> RESTART_ATTEMPT #{attempt} reason={reason}")

    send_alert(
        subject=f"[ERP 자동화] 장애 감지 - 재시작 시도 #{attempt}",
        body=(
            f"감지 시각: {now_str}\n"
            f"원인: {reason}\n"
            f"Heartbeat 나이: {age_min:.1f}분\n"
            f"재시작 시도: #{attempt}\n\n"
            f"워치독이 자동으로 복구를 시도합니다."
        ),
    )

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
        log_event("OK", f"RESTART_SUCCESS attempt={attempt}")
        return True
    except Exception as e:
        log_event("ERROR", f"Restart failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    if not acquire_watchdog_lock():
        return

    log_event("INFO", "=" * 70)
    log_event("INFO", f"Watchdog monitoring | timeout={TIMEOUT_MINUTES}m | interval={CHECK_INTERVAL}s")
    log_event("INFO", "=" * 70)

    consecutive_errors = 0

    try:
        while True:
            try:
                time_diff, content = check_heartbeat()

                if time_diff is None:
                    log_event("ERROR", content)
                    consecutive_errors += 1

                    if consecutive_errors >= 3:
                        log_event("ALERT", f"Consecutive heartbeat errors: {consecutive_errors}")
                        if kill_and_restart("heartbeat_missing", None, attempt=1):
                            consecutive_errors = 0
                            # Verify recovery after 60 s
                            time.sleep(60)
                            time_diff2, _ = check_heartbeat()
                            if time_diff2 is None:
                                log_event("ALERT", "Recovery unconfirmed (still missing) -> retry #2")
                                kill_and_restart("heartbeat_missing_retry", None, attempt=2)
                                time.sleep(60)
                else:
                    consecutive_errors = 0

                    if time_diff > timedelta(minutes=TIMEOUT_MINUTES):
                        age = time_diff.total_seconds()
                        log_event("INFO", f"Heartbeat snapshot: {content.strip().replace(chr(10), ' | ')}")

                        if kill_and_restart("heartbeat_stale", age, attempt=1):
                            # Wait 60 s then verify recovery
                            time.sleep(60)
                            time_diff2, _ = check_heartbeat()
                            if time_diff2 is not None and time_diff2 > timedelta(minutes=TIMEOUT_MINUTES):
                                age2 = time_diff2.total_seconds()
                                log_event("ALERT", f"Recovery unconfirmed (age={age2/60:.1f}m) -> retry #2")
                                kill_and_restart("heartbeat_stale_retry", age2, attempt=2)
                                time.sleep(60)
                    else:
                        log_event("OK", f"heartbeat age: {time_diff.total_seconds():.0f}s")

                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                log_event("ERROR", f"loop error: {e}")
                time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log_event("INFO", "Watchdog stopped by user")
    finally:
        release_watchdog_lock()


if __name__ == "__main__":
    main()
