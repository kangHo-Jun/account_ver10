@echo off
cd /d "%~dp0"
if exist ".\venv\Scripts\python.exe" (
  ".\venv\Scripts\python.exe" watchdog.py
) else if exist ".\.venv\Scripts\python.exe" (
  ".\.venv\Scripts\python.exe" watchdog.py
) else (
  python watchdog.py
)
