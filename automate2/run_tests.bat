@echo off
chcp 65001 > nul
title BOM Read Test Automation - Blue Site

:menu
cls
echo ========================================================
echo        BOM Accounting & Finance - Read Permission Automation
echo ========================================================
echo Target Site: https://reg1-bom-uat.thpc.cc/web/database/selector (Blue)
echo Total Read Test Cases: 168
echo.
echo [1] Run ALL Read Tests (Headed - see browser live)
echo [2] Run ALL Read Tests (Headless - background fast)
echo [3] Quick Test Run (First 5 test cases)
echo [4] Exit
echo.
set /p opt="Select option (1-4): "

if "%opt%"=="1" (
    echo.
    echo Running all 168 Read test cases in Headed mode...
    python run_read_tests.py
    pause
    goto menu
)
if "%opt%"=="2" (
    echo.
    echo Running all 168 Read test cases in Headless mode...
    python run_read_tests.py --headless
    pause
    goto menu
)
if "%opt%"=="3" (
    echo.
    echo Running Quick Test (5 cases)...
    python run_read_tests.py --limit 5
    pause
    goto menu
)
if "%opt%"=="4" (
    exit /b 0
)

echo Invalid choice, try again.
pause
goto menu
