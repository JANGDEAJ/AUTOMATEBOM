@echo off
title Launch 6 Role Browsers (BOM UAT)
cls
echo ========================================================
echo        BOM UAT Automation - Launch 6 Role Tabs
echo ========================================================
echo.
echo Select target environment branch/link:
echo.
echo   [1] HQ Link       (Super Admin HQ, Admin HQ, Supervisor, Super User, Cashier, Outsource)
echo   [2] Branch Link   (Super Admin Branch, Admin Branch, Supervisor, Super User, Cashier, Outsource)
echo.
set /p ENV_CHOICE="Enter environment choice (1 or 2): "

if "%ENV_CHOICE%"=="1" (
    set ENV_TYPE=HQ
) else if "%ENV_CHOICE%"=="2" (
    set ENV_TYPE=Branch
) else (
    echo Invalid choice. Defaulting to Branch Link...
    set ENV_TYPE=Branch
)

echo.
echo Select Database Code:
echo.
echo   [1] 13000  (Default)
echo   [2] 13140
echo.
set /p DB_CHOICE="Enter database choice (1 or 2): "

if "%DB_CHOICE%"=="2" (
    set DB_CODE=13140
) else (
    set DB_CODE=13000
)

echo.
echo Starting 6 browser tabs for Environment: %ENV_TYPE%, DB Code: %DB_CODE%...
python "%~dp0launch_6_roles.py" --env %ENV_TYPE% --db %DB_CODE%

echo.
echo Done! All 6 browser tabs logged in and at Home Page.
pause
