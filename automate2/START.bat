@echo off
chcp 65001 >nul
title BOM UAT Automation Suite
cd /d "%~dp0"

echo.
echo   ╔════════════════════════════════════════╗
echo   ║   BOM UAT Automation Suite             ║
echo   ║   Accounting ^& Finance                 ║
echo   ╚════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause & exit /b 1
)

:: Check playwright
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing playwright...
    pip install playwright -q
    playwright install chromium
)

:: Check flask
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing flask...
    pip install flask -q
)

:: Check openpyxl
python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing openpyxl...
    pip install openpyxl -q
)

echo.
echo   What would you like to do?
echo.
echo   [1] Open Web Dashboard (recommended)
echo   ─────────────────────────────────
echo   [2] Run ALL tests headless (CLI)
echo   [3] Run READ only headless (CLI)
echo   [4] Run CREATE only headless (CLI)
echo   [5] Run VALIDATE only headless (CLI)
echo   [6] Run SETTING only headless (CLI)
echo   [7] Run ALL tests headed/visible (CLI)
echo   ─────────────────────────────────
echo   [8] Quick test - 5 cases headed (CLI)
echo   [9] Quick test - 5 cases headless (CLI)
echo.
set /p choice="   Select (1-9): "
echo.

if "%choice%"=="1" (
    echo   Starting Web Dashboard...
    start "" "http://localhost:5000"
    cd improved\webapp
    python server.py
    goto :end
)

cd improved

if "%choice%"=="2" python run.py --headless
if "%choice%"=="3" python run.py --headless --type Read
if "%choice%"=="4" python run.py --headless --type Create
if "%choice%"=="5" python run.py --headless --type "Validate (approve/reject)"
if "%choice%"=="6" python run.py --headless --type "Setting (set approver/master)"
if "%choice%"=="7" python run.py
if "%choice%"=="8" python run.py --limit 5
if "%choice%"=="9" python run.py --limit 5 --headless

:end
echo.
echo   Done! Report saved to: improved\reports\test_results.xlsx
echo.
pause
