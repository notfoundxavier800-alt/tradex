@echo off
title TradeX - Cloudflare Live Launcher
color 0A
cls

echo.
echo  ============================================
echo   TradeX Signal Bot - Cloudflare Live Mode
echo  ============================================
echo.

:: Check if bot is already running on port 5000
echo  [1/3] Checking if TradeX bot is running...
powershell -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/status' -TimeoutSec 2 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if %errorlevel% == 0 (
    echo  Bot already running on port 5000!
    goto START_TUNNEL
)

:: Bot not running ? start it
echo  Bot not running. Starting now...
start "TradeX Bot" cmd /k "cd /d %~dp0 && python bot.py --no-browser"

echo  [2/3] Waiting for bot to be ready...
:WAIT_LOOP
timeout /t 3 /nobreak >nul
powershell -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/status' -TimeoutSec 2 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% == 0 goto START_TUNNEL
echo  Still waiting...
goto WAIT_LOOP

:START_TUNNEL
echo.
echo  [3/3] Bot is UP! Starting Cloudflare Tunnel...
echo.
echo  =====================================================
echo   YOUR PUBLIC URL WILL APPEAR IN ~5 SECONDS:
echo   Look for: https://xxxx.trycloudflare.com
echo   Copy it and open on any device worldwide!
echo  =====================================================
echo.

"%~dp0cloudflared.exe" tunnel --url http://127.0.0.1:5000

pause
