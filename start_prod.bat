@echo off
echo ========================================
echo   Account Automation - PRODUCTION MODE
echo ========================================
echo [INFO] Running in background every 30 mins.
echo.

cd /d %~dp0
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

start "Account_Automation" /min pythonw main.py

echo [INFO] Started in background. Check logs/ for status.
timeout /t 5
