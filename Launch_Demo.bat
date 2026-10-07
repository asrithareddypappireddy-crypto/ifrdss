@echo off
title IFRDSS Live Web Demo Launcher
echo ===================================================================
echo   Launching Intelligent Flood Rescue Decision Support System (IFRDSS)
echo ===================================================================
echo.
echo Starting Web Server on http://127.0.0.1:8080 ...
cd /d "%~dp0backend"
start http://127.0.0.1:8080
python -m uvicorn main:app --host 127.0.0.1 --port 8080
pause
