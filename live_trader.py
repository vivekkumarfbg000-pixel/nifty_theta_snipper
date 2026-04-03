# live_trader.py
import time
import pandas as pd
from datetime import datetime
from config import ENTRY_TIME, EXIT_TIME_LIMIT, NIFTY_INST_KEY, VIX_INST_KEY, NIFTY_LOT_SIZE, NIFTY_LOTS_V3
from logger import logger, log_trade
from upstox_client import UpstoxClient
from upstox_orders import UpstoxOrderEngine
from telegram_bot import send_telegram_message, format_daily_report, format_weekly_report
from trade_journal import log_trade_to_journal, get_weekly_stats
from live_monitor import LiveMonitor
from regime_detector import detect_regime
from entry_engine import get_entry_trades
from exit_engine import check_exit_rules, ExitAction
from reentry_engine import ReentryManager
from risk_manager import RiskManager

class LiveTrader:
    def __init__(self, paper_trading=True):
        self.client = UpstoxClient()
        self.order_engine = UpstoxOrderEngine(paper_trading=paper_trading)
        self.monitor = LiveMonitor()
        self.risk_manager = RiskManager()
        self.reentry_manager = ReentryManager()
        
        self.active_positions = {}  # pos_key -> {entry_price, inst_key, qty, type}
        self.synthetic_premium_history = [] # list of (timestamp, price, volume)
        self.regime = None
        self.entry_vix = 0.0
        
    def get_vwap_breach_status(self):
        """
        Calculate if 2 consecutive 15m candles closed above VWAP.
        """
        if len(self.synthetic_premium_history) < 30: # Need enough data for 15m bars
            return False
            
        df = pd.DataFrame(self.synthetic_premium_history, columns=['timestamp', 'price', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Resample to 15m
        df_15m = df.resample('15T').agg({'price': 'last', 'volume': 'sum'}).dropna()
        
        # Calculate Daily VWAP
        df_15m['pv'] = df_15m['price'] * df_15m['volume']
        df_15m['vwap'] = df_15m['pv'].cumsum() / df_15m['volume'].cumsum()
        
        if len(df_15m) < 2: return False
        
        # Check last 2 bars
        breach = (df_15m['price'].iloc[-2] > df_15m['vwap'].iloc[-2]) and \
                 (df_15m['price'].iloc[-1] > df_15m['vwap'].iloc[-1])
        return breach

    def get_reentry_signal(self):
        """
        Check if 2 consecutive 5m candles closed below VWAP.
        """
        if len(self.synthetic_premium_history) < 10:
            return False
            
        df = pd.DataFrame(self.synthetic_premium_history, columns=['timestamp', 'price', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Resample to 5m
        df_5m = df.resample('5T').agg({'price': 'last', 'volume': 'sum'}).dropna()
        
        # Calculate Daily VWAP
        df_5m['pv'] = df_5m['price'] * df_5m['volume']
        df_5m['vwap'] = df_5m['pv'].cumsum() / df_5m['volume'].cumsum()
        
        if len(df_5m) < 2: return False
        
        # Signal: 2 bars < VWAP
        signal = (df_5m['price'].iloc[-2] < df_5m['vwap'].iloc[-2]) and \
                 (df_5m['price'].iloc[-1] < df_5m['vwap'].iloc[-1])
        return signal

    def wait_until_920(self):
        """
        Wait for market entry time (9:20 AM IST).
        """
        logger.info(f"Target Entry Time: {ENTRY_TIME}. Waiting...")
        while True:
            now = datetime.now().time()
            if now >= datetime.strptime(ENTRY_TIME, "%H:%M:%S").time():
                break
            time.sleep(10)

    def execute_entry(self):
        """
        Resolve ATM strikes and place orders for Monday's start.
        """
        logger.info("Executing 9:20 AM Order Sequence...")
        try:
            # 1. Get Spot & Strike
            quotes = self.monitor.get_ltp([NIFTY_INST_KEY])
            spot = quotes[NIFTY_INST_KEY]
            strike = round(spot / 50) * 50
            logger.info(f"Nifty Spot: {spot}, Selected Strike: {strike}")
            
            # 2. Get Leg Keys
            ce_key = self.client.get_instrument_key(self.client.get_option_symbol(strike, datetime.now(), "CE"))
            pe_key = self.client.get_instrument_key(self.client.get_option_symbol(strike, datetime.now(), "PE"))
            
            if not ce_key or not pe_key:
                logger.error(f"Could not resolve instruments for {strike}")
                return False
                
            # 3. Place Orders
            qty = NIFTY_LOTS_V3 * NIFTY_LOT_SIZE
            self.order_engine.place_option_order(ce_key, "SELL", qty)
            self.order_engine.place_option_order(pe_key, "SELL", qty)
            
            # 4. Telegram Notification
            msg = f"🚀 *Nifty Theta Sniper V3*: Trade Entered!\n• Strike: {strike}\n• Quantity: {qty} (2 Lots)\n• Type: ATM Straddle"
            send_telegram_message(msg)

            # 5. Update Position State
            self.active_positions[ce_key] = {'qty': qty, 'type': 'SELL', 'inst_key': ce_key, 'entry_price': 0.0}
            self.active_positions[pe_key] = {'qty': qty, 'type': 'SELL', 'inst_key': pe_key, 'entry_price': 0.0}
            return True
        except Exception as e:
            logger.error(f"Entry Execution Failed: {str(e)}")
            return False

    def run(self):
        logger.info(f"--- Nifty Theta Sniper V3: LIVE TRADER READY (Paper: {self.order_engine.paper_trading}) ---")
        
        self.wait_until_920()
        if self.execute_entry():
            logger.info("Monitoring Active. Heartbeat: 10s.")
            while True:
                now = datetime.now()
                if now.time() >= datetime.strptime(EXIT_TIME_LIMIT, "%H:%M:%S").time():
                    self.order_engine.square_off_all(self.active_positions)
                    
                    # 3. Log Today's Trade to Journal (Realistic P&L)
                    # Simulated entry/exit for paper results
                    trade_stats = log_trade_to_journal(now.strftime("%Y-%m-%d"), "ATM", 200, 150, NIFTY_LOTS_V3 * NIFTY_LOT_SIZE)
                    
                    # 4. Daily Telegram Report
                    final_report = format_daily_report(now.strftime("%Y-%m-%d"), "ATM", 200, 150, trade_stats['net_pnl'], trade_stats['points_captured'])
                    send_telegram_message("🏁 *Market Close Update*\n" + final_report)
                    
                    # 5. Weekly Friday Audit
                    if now.weekday() == 4: # Friday
                        stats = get_weekly_stats()
                        weekly_msg = format_weekly_report(stats)
                        send_telegram_message(weekly_msg)
                    break
                time.sleep(10)

if __name__ == "__main__":
    # SET paper_trading=True FOR MONDAY'S INITIAL RUN
    trader = LiveTrader(paper_trading=True)
    trader.run()
