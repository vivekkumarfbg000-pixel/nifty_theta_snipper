# logger.py
import logging
import os
from datetime import datetime

# Setup log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Generate log filename based on current date
log_filename = os.path.join(LOG_DIR, f"strategy_{datetime.now().strftime('%Y-%m-%d')}.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ThetaSniper")

def log_trade(action, symbol, strike, quantity, price, reason):
    """
    Log a specific trade action.
    """
    message = f"[{action}] {symbol} @ {strike} | Qty: {quantity} | Price: {price} | Reason: {reason}"
    logger.info(message)

def log_regime(vix, adx, regime):
    """
    Log the detected market regime.
    """
    message = f"[REGIME] VIX: {vix} | ADX: {adx} | Mode: {regime}"
    logger.info(message)

def log_error(error_msg):
    """
    Log an error with traceback.
    """
    logger.error(error_msg, exc_info=True)
