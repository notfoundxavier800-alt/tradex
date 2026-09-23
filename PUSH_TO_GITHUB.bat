@echo off
title TradeX - 1-Click Push to GitHub for Render
color 0b
echo ===================================================================
echo     TradeX 24-Vector Infallible Engine - Push to GitHub
echo ===================================================================
echo.
echo 1. Open your browser and create a new repository on GitHub:
echo    https://github.com/new
echo    Repository name: tradex (Set to Public or Private)
echo.
set /p REPO_URL="2. Paste your GitHub repository URL here: "
if "%REPO_URL%"=="" (
    echo No URL entered. Exiting.
    pause
    exit /b
)

echo.
echo [1/3] Setting branch to main...
git branch -M main

echo [2/3] Linking remote repository...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [3/3] Pushing all files to GitHub...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ❌ Git push failed. If asked for credentials, use your GitHub username and Personal Access Token (PAT).
    echo Guide to create a token: https://github.com/settings/tokens
    pause
    exit /b
)

echo.
echo ===================================================================
echo  ✅ SUCCESS! Code is live on GitHub!
echo ===================================================================
echo.
echo Now deploy on Render in 30 seconds:
echo 1. Go to https://dashboard.render.com
echo 2. Click "New +" -> "Web Service"
echo 3. Select your "tradex" repository
echo 4. Render will auto-detect render.yaml and deploy for 100%% FREE!
echo.
pause
