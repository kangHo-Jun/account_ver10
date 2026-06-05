@echo off
cd /d "%~dp0"

echo [LOG] Starting watchdog...

REM Launch watchdog in background (singleton enforced inside watchdog.py via watchdog.lock)
start "" /B ".\.venv\Scripts\pythonw.exe" watchdog.py

timeout /t 3 /nobreak >nul
echo [OK] Watchdog launch command sent.
