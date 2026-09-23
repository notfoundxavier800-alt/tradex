@echo off
title TradeX Apex Predator - Live Terminal
color 0A
cls

echo =============================================================
echo   TRADEX QUANT TERMINAL - CWALLET PREDICTION APEX
echo =============================================================
echo.

echo [1/3] Checking TradeX Bot Server on port 5000...
powershell -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/status' -TimeoutSec 2 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if %errorlevel% == 0 (
    echo   [OK] Bot is already running on port 5000!
) else (
    echo   [..] Starting TradeX Bot daemon...
    start "TradeX Bot Engine" cmd /k "cd /d %~dp0 && python bot.py --no-browser"
    timeout /t 6 /nobreak >nul
)

echo.
echo [2/3] Connecting Institutional Cloudflare Tunnel...
echo =============================================================
echo   YOUR LIVE DASHBOARD IS RUNNING AT:
echo   Local:      http://127.0.0.1:5000
echo.
echo   Cloudflare Tunnel starting below...
echo =============================================================
echo.

"%~dp0cloudflared.exe" tunnel --url http://127.0.0.1:5000

pause
