@echo off
setlocal enabledelayedexpansion

REM ================================================
REM Daily restart script
REM ================================================

echo [LOG] Daily Restart Started...
echo [LOG] Restarting automation...

cd /d "%~dp0"

REM 1. Terminate only the tracked worker PID.
echo [LOG] Terminating existing process...
if exist runtime.lock (
    for /f %%I in (runtime.lock) do taskkill /F /PID %%I /T 2>nul
)
if %errorlevel% equ 0 (
    echo [OK] Existing process terminated.
) else (
    echo [INFO] No running process found.
)

REM 2. Wait and clean state files.
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

REM 3. Start the application.
echo [LOG] Starting the application...
start "" /B pythonw main.py

REM 4. Verify startup.
timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] Restart Successful.
) else (
    echo [ERROR] Restart Failed. Please check logs.
)

echo [LOG] Done.
echo ================================================
