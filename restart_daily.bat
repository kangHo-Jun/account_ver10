@echo off
setlocal enabledelayedexpansion

REM ================================================
REM 일일 자동 재시작 스크립트 (V10)
REM - 인코딩: ANSI (EUC-KR) 권장 또는 UTF-8 (BOM 없음)
REM ================================================

echo [LOG] Daily Restart Started...
echo [LOG] 재시작을 시작합니다.

cd /d "%~dp0"

REM 1. 기존 프로세스 종료
echo [LOG] Terminating existing processes...
taskkill /F /IM pythonw.exe /T 2>nul
if %errorlevel% equ 0 (
    echo [OK] Existing processes terminated.
) else (
    echo [INFO] No running processes found.
)

REM 2. 대기 및 파일 정리
echo [LOG] Waiting for 5 seconds...
timeout /t 5 /nobreak >nul

if exist runtime.lock (
    del runtime.lock
    echo [INFO] runtime.lock deleted.
)
if exist heartbeat.txt (
    del heartbeat.txt
    echo [INFO] heartbeat.txt deleted.
)

REM 3. 프로그램 실행
echo [LOG] Starting the application...
start /B pythonw main.py

REM 4. 실행 확인
timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] Restart Successful.
) else (
    echo [ERROR] Restart Failed. Please check logs.
)

echo [LOG] Done.
echo ================================================
pause

