@echo off
title Nifty Theta Sniper - VPS SETUP
echo ----------------------------------------------------
echo   Nifty Theta Sniper V3: Cloud Setup Utility
echo ----------------------------------------------------
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is NOT installed on this VPS.
    echo Please download and install Python 3.10+ from python.org first.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

echo [OK] Python detected.
echo.

:: 2. Install Requirements
echo [STEP 2] Installing necessary libraries (pandas, requests, upstox)...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Library installation failed. Check your internet connection.
    pause
    exit /b
)

echo.
echo [SUCCESS] Your Cloud PC is now configured!
echo ----------------------------------------------------
echo  Next Steps:
echo  1. Ensure config.py has your Token and Telegram ID.
echo  2. Run 'python live_trader.py' to start monitoring.
echo ----------------------------------------------------
pause
