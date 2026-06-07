@echo off
REM ================================================
REM ERP 자동화 종료 스크립트
REM ================================================

echo [LOG] ERP Automation Stopping...
echo [LOG] 프로그램을 종료합니다.

REM 프로세스 종료
taskkill /F /IM pythonw.exe /T 2>nul
if %errorlevel% equ 0 (
    echo [OK] Program stopped successfully.
) else (
    echo [INFO] No running process found.
)

echo [LOG] Done.
