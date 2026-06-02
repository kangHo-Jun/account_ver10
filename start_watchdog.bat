@echo off
cd /d "%~dp0"

echo [LOG] Starting watchdog...

REM Detect pythonw in venv, fall back to system pythonw
if exist ".\venv\Scripts\pythonw.exe" (
  set PYTHONW=.\venv\Scripts\pythonw.exe
) else if exist ".\.venv\Scripts\pythonw.exe" (
  set PYTHONW=.\.venv\Scripts\pythonw.exe
) else (
  set PYTHONW=pythonw
)

REM Launch watchdog in background (singleton enforced inside watchdog.py via watchdog.lock)
start "" /B %PYTHONW% watchdog.py

timeout /t 3 /nobreak >nul
echo [OK] Watchdog launch command sent.
