@echo off
chcp 65001 > nul
echo ========================================
echo 백업 및 프로그램 재시작
echo ========================================
echo.

echo [1/3] 현재 실행 중인 프로그램 종료...
taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo ✓ Python 프로세스 종료 완료
    timeout /t 2 /nobreak > nul
) else (
    echo - 실행 중인 Python 프로세스 없음
)
echo.

echo [2/3] 전체 폴더 백업 중...
if exist "c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107" (
    echo ! 기존 백업 폴더 발견 - 덮어쓰기
    rmdir /S /Q "c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107"
)
xcopy /E /I /Q "c:\Users\DSAI\Desktop\회계_ERP" "c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107"
echo ✓ 백업 완료: c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107
echo.

echo [3/3] 프로그램 재시작...
cd /d "c:\Users\DSAI\Desktop\회계_ERP"
start "이카운트 자동화" cmd /k "python main.py"
echo ✓ 프로그램 시작됨 (새 창)
echo.

echo ========================================
echo 완료!
echo - 백업 위치: c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107
echo - 문제 발생 시 rollback.bat 실행하세요
echo ========================================
echo.
timeout /t 3
exit
