@echo off
REM ================================================
REM ERP 자동화 시작 스크립트 (월~토 07:00)
REM ================================================

cd /d "%~dp0"

echo [LOG] ERP Automation Starting...
echo [LOG] 프로그램을 시작합니다.

REM 중복 실행 방지 확인
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [WARN] Program is already running. Skipping start.
    exit /b 0
)

REM 프로그램 실행
start /B pythonw main.py

REM 실행 확인
timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] Program started successfully.
) else (
    echo [ERROR] Failed to start program.
)

echo [LOG] Done.
