@echo off
chcp 65001 >nul
REM ================================================
REM 일일 자동 재시작 스크립트
REM - 매일 05:55에 Windows 작업 스케줄러로 실행
REM - 모든 pythonw 프로세스 종료 후 재시작
REM ================================================

echo [LOG] 일일 재시작 시작

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM 모든 pythonw 프로세스 종료
echo [LOG] 기존 프로세스 종료 중...
taskkill /F /IM pythonw.exe /T 2>nul
if %errorlevel% equ 0 (
    echo [OK] 프로세스 종료 완료
) else (
    echo [INFO] 실행 중인 프로세스 없음
)

REM 5초 대기
echo [LOG] 5초 대기 중...
timeout /t 5 /nobreak >nul

REM 락 파일 및 하트비트 파일 정리
if exist runtime.lock (
    del runtime.lock
    echo [INFO] 락 파일 삭제 완료
)
if exist heartbeat.txt (
    del heartbeat.txt
    echo [INFO] 하트비트 파일 삭제 완료
)

REM 프로그램 재시작
echo [LOG] 프로그램 재시작 중...
start /B pythonw main.py

REM 2초 대기 후 확인
timeout /t 2 /nobreak >nul

REM 프로세스 실행 확인
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] 재시작 성공
) else (
    echo [ERROR] 재시작 실패 - 수동 확인 필요
)

echo [LOG] 일일 재시작 완료
echo ================================================
