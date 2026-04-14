# vps_scheduler.py
import datetime
import time
import subprocess
import sys
import logging
import os
from daily_scheduler import check_market_open
from telegram_bot import send_telegram_message

# Setup log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
scheduler_log = os.path.join(LOG_DIR, "vps_scheduler.log")
launcher_output_log = os.path.join(LOG_DIR, "launcher_last_run.txt")

# Set up dedicated scheduler logger
scheduler_logger = logging.getLogger("VPSScheduler")
scheduler_logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
fh = logging.FileHandler(scheduler_log)
formatter = logging.Formatter('%(asctime)s - VPSScheduler - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
fh.setFormatter(formatter)
scheduler_logger.addHandler(sh)
scheduler_logger.addHandler(fh)

def run_vps_service():
    """
    Infinite loop daemon that checks the calendar every day and 
    starts the live trader at 09:14:00 AM.
    """
    scheduler_logger.info("Nifty Theta Sniper - VPS Auto-Scheduler Started 24/7.")
    send_telegram_message("🤖 *VPS Daemon Online*: Sniper is monitoring date and time 24/7.")

    already_run_today = False
    last_run_date = None
    last_heartbeat_hour = -1

    while True:
        now = datetime.datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")

        # Reset flag on a new day
        if current_date_str != last_run_date:
            already_run_today = False
            last_run_date = current_date_str
            scheduler_logger.info(f"New day detected: {current_date_str}. Flags reset.")

        # Hourly heartbeat in log
        if now.hour != last_heartbeat_hour:
            scheduler_logger.info(f"Heartbeat: Scheduler is active. Time: {now.strftime('%H:%M:%S')}")
            last_heartbeat_hour = now.hour

        is_open, reason = check_market_open(now)

        # Trigger conditions
        # Start exactly at 09:14 AM (or slightly after if delayed) to allow initialization before 9:20 AM
        if is_open and not already_run_today:
            if now.hour == 9 and 14 <= now.minute <= 20:
                msg = f"📈 *Nifty Theta Sniper*: Trading Day Detected! Injecting Live Bot at 09:14 AM."
                scheduler_logger.info(msg)
                send_telegram_message(msg)
                
                # Start the live trader bot using Popen so it runs non-blocking
                try:
                    # Capture stdout and stderr to a file so we can see why it might fail to start
                    with open(launcher_output_log, "w") as out:
                        subprocess.Popen([sys.executable, "live_trader.py"], 
                                         stdout=out, 
                                         stderr=subprocess.STDOUT)
                        
                    already_run_today = True
                    scheduler_logger.info("Bot Successfully Launched! Sleeping scheduler until next day.")
                    
                    # Sleep for the rest of the trading day to save CPU cycles on VPS
                    time.sleep(8 * 3600)  # Sleep 8 hours (until ~ 5 PM)
                except Exception as e:
                    err_msg = f"❌ *FATAL*: Failed to launch live_trader: {str(e)}"
                    scheduler_logger.error(err_msg)
                    send_telegram_message(err_msg)
                    time.sleep(60) # Don't loop crash

        # Check health every 60 seconds (reduced frequency to save logs)
        time.sleep(60)

if __name__ == "__main__":
    run_vps_service()
