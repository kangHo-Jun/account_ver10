@echo off
echo ========================================
echo   Account Automation V9.5 Installer
echo ========================================
echo.

echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
python --version

echo [2/5] Creating Virtual Environment...
if not exist venv (
    python -m venv venv
) else (
    echo Venv already exists.
)

echo [3/5] Installing Libraries...
call venv\Scripts\activate.bat
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing dependencies (Binary only mode)...
REM Force usage of pre-compiled wheels for ALL packages to avoid C++ Build Tools requirement
pip install --only-binary=:all: -r requirements.txt

echo [4/5] Installing Playwright Browser...
python -m playwright install chromium

echo [5/5] Creating Directories...
if not exist logs mkdir logs
if not exist sessions mkdir sessions
if not exist reports mkdir reports
if not exist data mkdir data

echo.
echo ========================================
echo   Installation Complete!
echo.
echo   [Next Steps]
echo   1. Edit config.json with your info.
echo   2. Run start_test.bat for testing.
echo   3. Run start_prod.bat for production.
echo ========================================
pause
