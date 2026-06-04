@echo off
REM ================================================
REM ERP automation stop script
REM ================================================

echo [LOG] ERP Automation Stopping...
echo [LOG] Stopping automation worker...

REM Stop only the PID tracked in runtime.lock.
if exist runtime.lock (
    for /f %%I in (runtime.lock) do taskkill /F /PID %%I /T 2>nul
)
if %errorlevel% equ 0 (
    echo [OK] Program stopped successfully.
) else (
    echo [INFO] No running process found.
)

echo [LOG] Done.
