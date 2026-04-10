@echo off
cd /d "%~dp0"
set PY_PATH=python
echo Starting Nifty Theta Sniper Dashboard...
start /b %PY_PATH% dashboard_api.py
echo Starting Trading Scheduler...
%PY_PATH% vps_scheduler.py
pause
