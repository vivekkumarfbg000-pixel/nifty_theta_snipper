@echo off
cd /d "%~dp0"
set PY_PATH=C:\Users\vivek\AppData\Local\Python\pythoncore-3.14-64\python.exe
echo Starting Nifty Theta Sniper Dashboard...
start /b %PY_PATH% dashboard_api.py
echo Starting Trading Scheduler...
%PY_PATH% daily_scheduler.py
pause
