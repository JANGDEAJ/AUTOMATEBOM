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
set /p CHOICE="Enter choice (1 or 2): "

if "%CHOICE%"=="1" (
    set ENV_TYPE=HQ
) else if "%CHOICE%"=="2" (
    set ENV_TYPE=Branch
) else (
    echo Invalid choice. Defaulting to Branch Link...
    set ENV_TYPE=Branch
)

echo.
echo Starting 6 browser tabs for environment: %ENV_TYPE%...
python "%~dp0launch_6_roles.py" --env %ENV_TYPE%

echo.
echo Done! All 6 browser tabs logged in and at Home Page.
pause
