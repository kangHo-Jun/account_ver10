@echo off
cd /d "%~dp0"

echo [LOG] ERP Automation Starting...

REM Skip when already running
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
  echo [WARN] Program is already running. Skipping start.
  exit /b 0
)

REM Cleanup stale files/processes
del /f /q runtime.lock >nul 2>&1
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
