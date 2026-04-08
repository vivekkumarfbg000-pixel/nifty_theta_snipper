# daily_scheduler.py
import datetime
import time
import subprocess
from logger import logger
from telegram_bot import send_telegram_message

# NSE Holidays 2026 (Partial List for Q1/Q2)
NSE_HOLIDAYS_2026 = [
    "2026-01-26", # Republic Day
    "2026-03-06", # Holi
    "2026-03-27", # Id-ul-Fitr (Ramadan Eid)
    "2026-03-31", # Mahavir Jayanti
    "2026-04-03", # Good Friday (TODAY)
    "2026-04-14", # Dr. Baba Saheb Ambedkar Jayanti
    "2026-05-01", # Maharashtra Day
]

def check_market_open(date_obj):
    """
    Check if today is a trading day.
    """
    date_str = date_obj.strftime("%Y-%m-%d")
    if date_obj.weekday() >= 5: # Saturday/Sunday
        return False, "Weekend"
    if date_str in NSE_HOLIDAYS_2026:
        return False, f"NSE Holiday: {date_str}"
    return True, "Trading Day"

def run_scheduler():
    """
    Morning heartbeat to start the trade engine.
    """
    # 1. Check Today's Date
    now = datetime.datetime.now()
    is_open, reason = check_market_open(now)
    
    if not is_open:
        msg = f"🛡️ *Nifty Theta Sniper*: Market is Closed today ({reason}). No trades planned."
        logger.info(msg)
        send_telegram_message(msg)
        return

    # Daily Execution
    msg = f"☀️ *Nifty Theta Sniper*: Good Morning! Trading Day Detected. Starting Live Monitoring at 9:15 AM."
    send_telegram_message(msg)
    
    # Start the live trader bot
    subprocess.Popen(["python", "live_trader.py"])

if __name__ == "__main__":
    run_scheduler()
