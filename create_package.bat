@echo off
setlocal
echo ========================================
echo   Account Automation Package Creator
echo ========================================

set VERSION=9.5
set PACKAGE_NAME=Account_Automation_V%VERSION%
set TEMP_DIR=package_temp

if exist %TEMP_DIR% rmdir /s /q %TEMP_DIR%
mkdir %TEMP_DIR%

echo [INFO] Copying files...
copy main.py %TEMP_DIR%\
copy config.example.json %TEMP_DIR%\
copy requirements.txt %TEMP_DIR%\
copy install.bat %TEMP_DIR%\
copy start_test.bat %TEMP_DIR%\
copy start_prod.bat %TEMP_DIR%\
copy stop.bat %TEMP_DIR%\
copy README.md %TEMP_DIR%\

xcopy core %TEMP_DIR%\core /E /I /H /Y
xcopy modules %TEMP_DIR%\modules /E /I /H /Y
xcopy utils %TEMP_DIR%\utils /E /I /H /Y

mkdir %TEMP_DIR%\logs
mkdir %TEMP_DIR%\sessions
mkdir %TEMP_DIR%\reports
mkdir %TEMP_DIR%\data

echo [INFO] Creating Zip...
powershell -Command "Compress-Archive -Path %TEMP_DIR%\* -DestinationPath %PACKAGE_NAME%.zip -Force"

rmdir /s /q %TEMP_DIR%

echo.
echo ========================================
echo   Packaging Complete: %PACKAGE_NAME%.zip
echo ========================================
pause
