@echo off
title tradex
color 0b
echo ============================================================
echo   tradex - 99%% Institutional Quantitative Trading Engine
echo ============================================================
echo.
echo Starting tradex trading terminal...
echo.

python -c "import flask, flask_socketio, pandas, websocket" >nul 2>&1
if %errorlevel% neq 0 (
    echo [Setup] Installing required Python libraries...
    pip install -r requirements.txt
    echo [Setup] Libraries installed successfully!
    echo.
)

echo [Boot] Launching tradex...
python bot.py
pause
