@echo off
title BOM UAT Dashboard
chcp 65001 >nul
cd /d "%~dp0"
echo Starting BOM UAT Dashboard...
echo Open your browser: http://localhost:5000
start "" "http://localhost:5000"
python server.py
pause
