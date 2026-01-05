@echo off
echo ========================================
echo   Account Automation - STOP Processes
echo ========================================

taskkill /F /IM pythonw.exe /T

echo.
echo [INFO] All automation processes terminated.
pause
