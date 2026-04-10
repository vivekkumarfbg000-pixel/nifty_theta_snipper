# vps_scheduler.py
import datetime
import time
import subprocess
import sys
import logging
from daily_scheduler import check_market_open
from telegram_bot import send_telegram_message

# Set up simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VPSScheduler - %(levelname)s - %(message)s'
)

def run_vps_service():
    """
    Infinite loop daemon that checks the calendar every day and 
    starts the live trader at 09:14:00 AM.
    """
    logging.info("Nifty Theta Sniper - VPS Auto-Scheduler Started 24/7.")
    send_telegram_message("VPS Daemon Online: Sniper is monitoring date and time 24/7.")

    already_run_today = False
    last_run_date = None

    while True:
        now = datetime.datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")

        # Reset flag on a new day
        if current_date_str != last_run_date:
            already_run_today = False
            last_run_date = current_date_str

        is_open, reason = check_market_open(now)

        # Trigger conditions
        # Start exactly at 09:14 AM (or slightly after if delayed) to allow initialization before 9:20 AM
        if is_open and not already_run_today:
            if now.hour == 9 and 14 <= now.minute <= 20:
                msg = f"Nifty Theta Sniper: Trading Day Detected! Injecting Live Bot at 09:14 AM."
                logging.info(msg)
                send_telegram_message(msg)
                
                # Start the live trader bot using Popen so it runs non-blocking
                try:
                    subprocess.Popen([sys.executable, "live_trader.py"])
                    already_run_today = True
                    logging.info("Bot Successfully Launched! Sleeping scheduler until next day.")
                    
                    # Sleep for the rest of the trading day to save CPU cycles on VPS
                    time.sleep(8 * 3600)  # Sleep 8 hours (until ~ 5 PM)
                except Exception as e:
                    err_msg = f"FATAL: Failed to launch live_trader: {str(e)}"
                    logging.error(err_msg)
                    send_telegram_message(err_msg)
                    time.sleep(60) # Don't loop crash

        # Check health every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    run_vps_service()
