@echo off
cd /d "%~dp0"
echo Starting Nifty Theta Sniper Dashboard...
start /b python dashboard_api.py
echo Starting Trading Scheduler...
python daily_scheduler.py
pause
