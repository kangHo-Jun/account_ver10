@echo off
cd /d "%~dp0"

echo [LOG] ERP Automation Starting...

REM Skip only when the PID in runtime.lock is still alive.
if exist runtime.lock (
  for /f %%I in (runtime.lock) do (
    tasklist /FI "PID eq %%I" | find "%%I" >nul
    if not errorlevel 1 (
      echo [WARN] Program is already running. Skipping start.
      exit /b 0
    )
  )
)

REM Cleanup stale state before relaunch.
del /f /q runtime.lock >nul 2>&1

REM Start the worker in the background.
start "" /B pythonw main.py

timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %errorlevel% equ 0 (
  echo [OK] Program started successfully.
) else (
  echo [ERROR] Failed to start program.
)

echo [LOG] Done.
