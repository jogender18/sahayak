@echo off
title Sahayak Wage Agreement App & Public Tunnel
cd /d "%~dp0"
echo ===================================================================
echo   Starting Sahayak (सहायक / సహాయక్) Wage Agreement App...
echo ===================================================================
echo.
start /B .\.venv\Scripts\python.exe app.py
timeout /t 2 /nobreak >nul
start /B .\.venv\Scripts\python.exe tunnel_manager.py
timeout /t 5 /nobreak >nul

set /p PUBLIC_URL=<public_url.txt
echo.
echo ===================================================================
echo   LOCAL ACCESS:  http://127.0.0.1:5000
echo   PUBLIC ACCESS: %PUBLIC_URL%
echo ===================================================================
echo.
start http://127.0.0.1:5000
echo App and Public Tunnel are running in background. Press any key to stop.
pause
