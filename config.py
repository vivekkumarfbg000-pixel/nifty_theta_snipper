import os
from dotenv import load_dotenv

# Load secret environment variables
load_dotenv()

"""
Configuration for Nifty Theta Sniper v2.
All parameters can be tuned here.
"""

# Portfolio Management
TOTAL_CAPITAL = 500000  # ₹5,00,000
MAX_DAILY_LOSS_PCT = 0.03  # 3% of capital
MAX_MONTHLY_LOSS_PCT = 0.05  # 5% of capital

# Broker Choice (Set to "UPSTOX", "ALICE_BLUE", or "WEBHOOK")
BROKER = os.getenv("BROKER", "WEBHOOK") 
PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true" # ₹0 Real Money if True

# Upstox API
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
NIFTY_INST_KEY = "NSE_INDEX|Nifty 50"
VIX_INST_KEY = "NSE_INDEX|India VIX"

# Alice Blue API
ALICE_BLUE_USER_ID = os.getenv("ALICE_BLUE_USER_ID")
ALICE_BLUE_API_KEY = os.getenv("ALICE_BLUE_API_KEY")
ALICE_BLUE_API_SECRET = os.getenv("ALICE_BLUE_API_SECRET")
ALICE_BLUE_TOTP_KEY = os.getenv("ALICE_BLUE_TOTP_KEY")
ALICE_NIFTY_TSYMBOL = "Nifty 50"

# Webhook Bridge (1lyalgos)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://api.1lyalgos.com/v3/webhook/tradingview/14364086-972f-45f8-acc9-bf90a751b7111775474149")
# Placeholder format for 1lyalgos (Update this if needed!)
WEBHOOK_PAYLOAD_FORMAT = {
    "symbol": "{symbol}",
    "action": "{side}",
    "type": "MARKET",
    "quantity": "{qty}",
    "strategy_id": "SNIPER_V3"
}

# Strategy Rules (Regime Thresholds)
VIX_THRESHOLD_CALM = 14.0
VIX_THRESHOLD_NORMAL = 20.0
ADX_THRESHOLD_TREND = 25.0

# Stop-Loss Percentages
SL_PCT_STRADDLE = 0.30  # 30%
SL_PCT_STRANGLE = 0.40  # 40%
SL_PCT_IRON_CONDOR = 0.60  # 60% of Max Risk

# Take-Profit Percentages
TP_PCT_STRADDLE = 0.50  # 50% target
TP_PCT_STRANGLE = 0.60  # 60% target
TP_PCT_IRON_CONDOR = 0.50  # 50% target

# Timing
OPENING_TIME = "09:15:00"
ENTRY_TIME = "09:20:00"
EXIT_TIME_LIMIT = "15:15:00"
EARLY_PROFIT_TIME = "14:30:00"
EARLY_PROFIT_PCT = 0.40  # 40% of premium

# VWAP Exit Logic
VWAP_TIMEFRAME = "15T"  # 15 minutes (Pandas offset frequency)
VWAP_EXIT_CANDLES = 2
VWAP_REENTRY_TIMEFRAME = "5T"  # 5 minutes
VWAP_REENTRY_CANDLES = 2

# Re-Entry Settings
MAX_REENTRIES_PER_DAY = 1
REENTRY_COOLDOWN_MINUTES = 15
MAX_REENTRY_TIME = "13:30:00"
REENTRY_POSITION_SIZE_MODIFIER = 0.5  # 50% size

# Costs (Effective April 2026)
STT_SELL_SIDE_PCT = 0.0015  # 0.15% of premium
BROKERAGE_PER_ORDER = 20.0
EXCHANGE_TRANSACTION_MODIFIER = 0.0000322  # ₹3.22/lakh
GST_PCT = 0.18

# 6-Month Training & Friction
SLIPPAGE_PER_LEG = 0.5  # 0.5 points per strike (Exit/Entry)
BROKERAGE_PER_ORDER = 20 # Flat ₹20 (Upstox/Zerodha)
TRADES_CSV_PATH = "trades_journal.csv"

# Telegram Reporting
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# V3 Strategy (Refined)
NIFTY_LOTS_V3 = 2
TRAILING_SL_TRIGGER_AMT = 1500  # ₹1,500 Profit
TRAILING_SL_V3_EXIT_CANDLES = 1 # Tighten to 1 candle once triggered

# Instruments
NIFTY_LOT_SIZE = 65  # UPDATED: NSE Lot size as of April 2026
NIFTY_SYMBOLS = ["NIFTY"]
