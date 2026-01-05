@echo off
chcp 65001 >nul
echo ========================================
echo   Account Automation - TEST MODE
echo ========================================
echo [INFO] Browser visible, NO real save (F8).
echo.

cd /d %~dp0

if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found! 
    echo Please run install.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating environment...
call venv\Scripts\activate.bat

echo [INFO] Starting Python script...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Program terminated with error code: %errorlevel%
)

echo.
echo ========================================
echo   Process Finished.
echo ========================================
pause
