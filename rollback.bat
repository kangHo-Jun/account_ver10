@echo off
chcp 65001 > nul
echo ========================================
echo 롤백 시작...
echo ========================================
echo.

echo [1/3] Python 프로세스 종료 중...
taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo ✓ Python 프로세스 종료 완료
) else (
    echo - 실행 중인 Python 프로세스 없음
)
echo.

echo [2/3] 백업에서 복원 중...
if exist "c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107" (
    xcopy /E /Y "c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107\*" "c:\Users\DSAI\Desktop\회계_ERP\"
    echo ✓ 복원 완료
) else (
    echo ✗ 백업 폴더를 찾을 수 없습니다!
    echo   백업 경로: c:\Users\DSAI\Desktop\회계_ERP_BACKUP_20260107
    pause
    exit /b 1
)
echo.

echo [3/3] 완료!
echo ========================================
echo 롤백이 완료되었습니다.
echo 이제 프로그램을 다시 시작하세요.
echo ========================================
echo.
pause
