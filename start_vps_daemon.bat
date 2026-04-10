@echo off
title Nifty Theta Sniper VPS 24/7 Daemon
cd /d "%~dp0"
set PY_PATH=python
echo ========================================================
echo   NIFTY THETA SNIPER - AWS VPS AUTOMATION
echo ========================================================
echo.
echo Launching the VPS Scheduler...
echo This window will stay open and monitor market time 24/7.
echo Do not close this window!
echo.
:loop
%PY_PATH% vps_scheduler.py
echo Scheduler crashed or exited! Restarting in 10 seconds...
timeout /t 10
goto loop
