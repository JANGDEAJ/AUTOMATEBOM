@echo off
chcp 65001 >nul
title BOM UAT Automation Suite
cd /d "%~dp0"

echo.
echo   BOM UAT Automation Suite
echo   Accounting ^& Finance
echo.

:: Check if server already running
powershell -Command "try { Invoke-WebRequest http://localhost:5000 -UseBasicParsing -TimeoutSec 2 | Out-Null; Write-Host 'SERVER_UP' } catch { Write-Host 'SERVER_DOWN' }" > %TEMP%\bom_check.txt 2>&1
set /p SERVER_STATUS=<%TEMP%\bom_check.txt

echo   What would you like to do?
echo.
echo   [1] Open Web Dashboard (http://localhost:5000)
echo   -----------------------------------------------
echo   [2] Run ALL tests headless (CLI)
echo   [3] Run READ only headless (CLI)
echo   [4] Run CREATE only headless (CLI)
echo   [5] Run VALIDATE only headless (CLI)
echo   [6] Run SETTING only headless (CLI)
echo   [7] Run ALL tests headed/visible (CLI)
echo   -----------------------------------------------
echo   [8] Quick test - 5 cases headless (CLI)
echo   [9] Restart web server
echo.
set /p choice="   Select (1-9): "
echo.

if "%choice%"=="1" (
    if "%SERVER_STATUS%"=="SERVER_UP" (
        echo   Server already running - opening browser...
    ) else (
        echo   Starting server...
        start "" /min cmd /c "cd /d "%~dp0improved\webapp" && python server.py"
        timeout /t 3 /nobreak >nul
    )
    start "" "http://localhost:5000"
    goto :end
)

if "%choice%"=="9" (
    echo   Stopping old server if any...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /PID %%a /F 2>nul
    timeout /t 2 /nobreak >nul
    echo   Starting fresh server...
    start "" /min cmd /c "cd /d "%~dp0improved\webapp" && python server.py"
    timeout /t 3 /nobreak >nul
    start "" "http://localhost:5000"
    goto :end
)

cd /d "%~dp0improved"
if "%choice%"=="2" python run.py --headless
if "%choice%"=="3" python run.py --headless --type Read
if "%choice%"=="4" python run.py --headless --type Create
if "%choice%"=="5" python run.py --headless --type "Validate (approve/reject)"
if "%choice%"=="6" python run.py --headless --type "Setting (set approver/master)"
if "%choice%"=="7" python run.py
if "%choice%"=="8" python run.py --limit 5 --headless

:end
echo.
pause
