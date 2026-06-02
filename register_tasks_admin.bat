@echo off
:: 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] 이 파일을 우클릭 → "관리자 권한으로 실행" 하세요.
  pause
  exit /b 1
)

set BAT_DIR=%~dp0
if "%BAT_DIR:~-1%"=="\" set BAT_DIR=%BAT_DIR:~0,-1%

echo [LOG] Task Scheduler 등록 시작...

REM 기존 충돌 작업 제거
schtasks /delete /tn "ERP 자동화 일일 재시작" /f >nul 2>&1
schtasks /delete /tn "ERP 자동화 메인" /f >nul 2>&1
schtasks /delete /tn "ERP 자동화 워치독" /f >nul 2>&1

REM ① 메인 자동화 — 부팅 후 1분 지연
schtasks /create ^
  /tn "ERP 자동화 메인" ^
  /tr "cmd.exe /c \"%BAT_DIR%\start_automation.bat\"" ^
  /sc ONSTART ^
  /delay 0000:01 ^
  /rl HIGHEST ^
  /ru "%USERNAME%" ^
  /it /f

if %errorlevel% equ 0 (
  echo [OK] 등록 성공: ERP 자동화 메인
) else (
  echo [ERROR] 등록 실패: ERP 자동화 메인
)

REM ② 워치독 — 부팅 후 2분 지연
schtasks /create ^
  /tn "ERP 자동화 워치독" ^
  /tr "cmd.exe /c \"%BAT_DIR%\start_watchdog.bat\"" ^
  /sc ONSTART ^
  /delay 0000:02 ^
  /rl HIGHEST ^
  /ru "%USERNAME%" ^
  /it /f

if %errorlevel% equ 0 (
  echo [OK] 등록 성공: ERP 자동화 워치독
) else (
  echo [ERROR] 등록 실패: ERP 자동화 워치독
)

echo.
echo === 등록된 작업 확인 ===
schtasks /query /tn "ERP 자동화 메인" /fo LIST
echo ---
schtasks /query /tn "ERP 자동화 워치독" /fo LIST

echo.
echo [OK] 완료. 창을 닫아도 됩니다.
pause
