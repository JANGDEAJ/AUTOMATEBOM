@echo off
title BOM UAT Automation Suite
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  BOM UAT Automation Suite (Improved)
echo ============================================
echo.
echo  [1] Run ALL tests (headed)
echo  [2] Run ALL tests (headless)
echo  [3] Run READ only (headed)
echo  [4] Run CREATE only (headed)
echo  [5] Run VALIDATE only (headed)
echo  [6] Run SETTING only (headed)
echo  [7] Run ALL headless - Super Admin only
echo  [8] Quick test - first 5 cases (headed)
echo.
set /p choice="Select option (1-8): "

if "%choice%"=="1" python run.py
if "%choice%"=="2" python run.py --headless
if "%choice%"=="3" python run.py --type Read
if "%choice%"=="4" python run.py --type Create
if "%choice%"=="5" python run.py --type "Validate (approve/reject)"
if "%choice%"=="6" python run.py --type "Setting (set approver/master)"
if "%choice%"=="7" python run.py --headless --role "Super Admin"
if "%choice%"=="8" python run.py --limit 5

echo.
echo Done!
pause
