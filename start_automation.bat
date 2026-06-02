@echo off
cd /d "%~dp0"

echo [LOG] ERP Automation Starting...

REM Check runtime.lock to see if main.py is actually running (not just any pythonw.exe)
if exist "runtime.lock" (
  set /p LOCK_PID=<runtime.lock
  tasklist /FI "PID eq %LOCK_PID%" 2>nul | find "%LOCK_PID%" >nul
  if %errorlevel% equ 0 (
    echo [WARN] Main automation (PID %LOCK_PID%) is already running. Skipping start.
    exit /b 0
  )
  echo [LOG] Stale runtime.lock detected (PID %LOCK_PID% not running). Cleaning up.
  del /f /q runtime.lock >nul 2>&1
)

REM Cleanup stale Chrome processes
taskkill /F /IM chrome.exe /T >nul 2>&1

REM Start worker
start "" /B pythonw main.py

timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
  echo [OK] Program started successfully.
) else (
  echo [ERROR] Failed to start program.
)

echo [LOG] Done.
