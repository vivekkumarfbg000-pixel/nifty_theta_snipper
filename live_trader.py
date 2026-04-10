# live_trader.py
import time
import pandas as pd
from datetime import datetime
from config import OPENING_TIME, ENTRY_TIME, EXIT_TIME_LIMIT, NIFTY_INST_KEY, VIX_INST_KEY, NIFTY_LOT_SIZE, NIFTY_LOTS_V3, BROKER, ALICE_NIFTY_TSYMBOL, PAPER_TRADING
from logger import logger, log_trade
from upstox_helper import UpstoxClient
from upstox_orders import UpstoxOrderEngine
from alice_blue_helper import AliceBlueClient
from alice_blue_orders import AliceBlueOrderEngine
from webhook_orders import WebhookOrderEngine
from telegram_bot import send_telegram_message, format_daily_report, format_weekly_report, format_entry_alert, format_hourly_status
from trade_journal import log_trade_to_journal, get_weekly_stats
from live_monitor import LiveMonitor
from regime_detector import detect_regime
from entry_engine import get_entry_trades
from exit_engine import check_exit_rules, ExitAction
from reentry_engine import ReentryManager
from risk_manager import RiskManager

class LiveTrader:
    def __init__(self, paper_trading=True):
        self.broker = BROKER
        if self.broker == "ALICE_BLUE":
            self.client = AliceBlueClient()
            self.order_engine = AliceBlueOrderEngine(paper_trading=paper_trading)
            self.nifty_key = ALICE_NIFTY_TSYMBOL
        elif self.broker == "WEBHOOK":
            # Use Webhook for orders, Upstox for data
            self.client = UpstoxClient()
            self.order_engine = WebhookOrderEngine(paper_trading=paper_trading)
            self.nifty_key = NIFTY_INST_KEY
        else:
            self.client = UpstoxClient()
            self.order_engine = UpstoxOrderEngine(paper_trading=paper_trading)
            self.nifty_key = NIFTY_INST_KEY

        self.monitor = LiveMonitor()
        self.risk_manager = RiskManager()
        self.reentry_manager = ReentryManager()
        
        self.active_positions = {}  # pos_key -> {entry_price, inst_key, qty, type, instrument}
        self.synthetic_premium_history = [] # list of (timestamp, price, volume)
        self.regime = None
        self.entry_vix = 0.0
        self.last_hourly_msg_hour = -1
        
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

    def wait_until(self, target_time_str, label="Entry"):
        """
        Wait for a specific time (HH:MM:SS format).
        """
        logger.info(f"Waiting for {label} Time: {target_time_str}...")
        while True:
            now = datetime.now().time()
            if now >= datetime.strptime(target_time_str, "%H:%M:%S").time():
                break
            time.sleep(10)

    def execute_entry(self):
        """
        Resolve ATM strikes and place orders.
        """
        logger.info(f"Executing Late Entry Order Sequence for {self.broker}...")
        try:
            # 1. Get Spot & Strike
            quotes = self.monitor.get_ltp([self.nifty_key])
            spot = quotes.get(self.nifty_key)
            if not spot:
                logger.error(f"Failed to get Spot price for {self.nifty_key}")
                return False
                
            strike = round(spot / 50) * 50
            logger.info(f"Nifty Spot: {spot}, Selected Strike: {strike}")
            
            # 2. Get Leg Keys/Instruments
            from datetime import timedelta
            today = datetime.now()
            days_until_thursday = (3 - today.weekday()) % 7
            expiry_date = today + timedelta(days=days_until_thursday)
            
            if self.broker == "ALICE_BLUE":
                # Alice Blue specific resolution
                # Symbols are typically like NIFTY24APR20000CE
                # We'll use a generic constructor for now or search
                expiry_str = expiry_date.strftime("%d%b%y").upper() # 10APR24
                ce_symbol = f"NIFTY{expiry_str}{strike}CE"
                pe_symbol = f"NIFTY{expiry_str}{strike}PE"
                
                ce_inst = self.client.get_instrument(ce_symbol)
                pe_inst = self.client.get_instrument(pe_symbol)
                
                ce_key, pe_key = ce_symbol, pe_symbol
                ce_val, pe_val = ce_inst, pe_inst
            else:
                ce_val, ce_symbol = self.client.get_instrument_key(strike=strike, expiry_date=expiry_date, option_type="CE")
                pe_val, pe_symbol = self.client.get_instrument_key(strike=strike, expiry_date=expiry_date, option_type="PE")
                ce_key, pe_key = ce_val, pe_val

            if not ce_val or not pe_val:
                if self.order_engine.paper_trading:
                    logger.warning(f"Could not resolve instruments. Falling back to MOCK for Paper Trading.")
                    ce_key, pe_key = f"MOCK_{strike}CE", f"MOCK_{strike}PE"
                    ce_val, pe_val = ce_key, pe_key
                else:
                    logger.error(f"Could not resolve instruments for {strike}")
                    return False
            
            # 3. Place Orders
            qty = NIFTY_LOTS_V3 * NIFTY_LOT_SIZE
            self.order_engine.place_option_order(ce_val, "SELL", qty)
            self.order_engine.place_option_order(pe_val, "SELL", qty)
            
            # 4. Fetch Real Entry Prices for Reporting
            entry_quotes = self.monitor.get_ltp([ce_key, pe_key])
            ce_entry = entry_quotes.get(ce_key)
            pe_entry = entry_quotes.get(pe_key)
            
            if ce_entry is None or pe_entry is None:
                # Abort even in Paper Trading: Using dummy premiums causes fake P&L tracking and crashes the loop
                logger.error(f"Critical Error: Could not fetch real-time entry LTP for {ce_key}/{pe_key}. Instrument may be illiquid. Aborting.")
                from telegram_bot import send_telegram_message
                send_telegram_message(f"🚨 *TRADE ABORTED*: Failed to fetch live premiums for selected strike. Check API connectivity or token.")
                return False

            # 5. Telegram Notification
            total_entry_premium = ce_entry + pe_entry
            msg = format_entry_alert(self.broker, strike, qty, total_entry_premium, self.order_engine.paper_trading)
            send_telegram_message(msg)

            # 6. Update Position State
            self.active_positions[ce_key] = {'qty': qty, 'type': 'SELL', 'inst_key': ce_key, 'entry_price': ce_entry, 'instrument': ce_val}
            self.active_positions[pe_key] = {'qty': qty, 'type': 'SELL', 'inst_key': pe_key, 'entry_price': pe_entry, 'instrument': pe_val}
            return True
        except Exception as e:
            logger.error(f"Entry Execution Failed: {str(e)}")
            return False

    def run(self):
        logger.info(f"--- Nifty Theta Sniper V3: LIVE TRADER READY (Paper: {self.order_engine.paper_trading}) ---")
        
        self.wait_until(OPENING_TIME, "Market Opening")
        send_telegram_message(f"☀️ *Nifty Theta Sniper Bot is Online!*\nBroker: {self.broker}\nWaiting for 09:20 Entry...")

        self.wait_until(ENTRY_TIME, "Trade Entry")
        if self.execute_entry():
            logger.info("Monitoring Active. Heartbeat: 10s.")
            while True:
                now = datetime.now()
                current_time_str = now.strftime("%H:%M:%S")
                
                # --- Hourly Status Update ---
                if now.minute == 0 and now.hour != self.last_hourly_msg_hour:
                    self.send_hourly_update(now)
                    self.last_hourly_msg_hour = now.hour
                
                # --- Monitoring & Risk Management ---
                try:
                    # 1. Fetch current prices for all active legs
                    inst_keys = list(self.active_positions.keys())
                    current_prices = self.monitor.get_ltp(inst_keys)
                    
                    # 2. Check exit rules (SL / TP / Time)
                    # Note: self.regime might be None if no VIX data, check_exit_rules should handle it
                    positions_summary = {k: v['entry_price'] for k, v in self.active_positions.items()}
                    actions = check_exit_rules(positions_summary, current_prices, current_time_str, self.regime)
                    
                    for pos_key, action_data in actions.items():
                        action = action_data['action']
                        reason = action_data['reason']
                        
                        if action == ExitAction.EXIT_LEG:
                            logger.info(f"Stopping Leg {pos_key} (Type: {self.active_positions[pos_key]['type']}) due to {reason}")
                            self.order_engine.place_option_order(self.active_positions[pos_key]['instrument'], "BUY", self.active_positions[pos_key]['qty'])
                            del self.active_positions[pos_key]
                            
                        elif action == ExitAction.EXIT_ALL:
                            logger.info(f"Closing All Positions due to {reason}")
                            self.order_engine.square_off_all(self.active_positions)
                            self.active_positions.clear()
                            break

                except Exception as e:
                    logger.error(f"Monitoring Loop Error: {str(e)}")

                # --- Market Close Clean-up ---
                if current_time_str >= EXIT_TIME_LIMIT or not self.active_positions:
                    if self.active_positions:
                        logger.info(f"Market Close reached ({EXIT_TIME_LIMIT}). Squaring off remaining positions.")
                        self.order_engine.square_off_all(self.active_positions)
                    
                    # 2. Fetch Real Exit Prices for Reporting
                    exit_quotes = self.monitor.get_ltp(list(self.active_positions.keys())) if self.active_positions else {}
                    
                    total_entry_premium = sum(pos['entry_price'] for pos in self.active_positions.values() if isinstance(pos['entry_price'], (int, float))) if self.active_positions else 0.0
                    total_exit_premium = sum(exit_quotes.get(k, pos['entry_price']) for k, pos in self.active_positions.items() if isinstance(exit_quotes.get(k, pos['entry_price']), (int, float))) if self.active_positions else 0.0
                    
                    # 3. Log Today's Trade to Journal
                    trade_stats = log_trade_to_journal(
                        date=now.strftime("%Y-%m-%d"), 
                        strike="ATM", 
                        entry_price=total_entry_premium, 
                        exit_price=total_exit_premium, 
                        quantity=NIFTY_LOTS_V3 * NIFTY_LOT_SIZE,
                        strategy="STRADDLE",
                        regime="NORMAL", # You could use self.current_regime here if tracked
                        is_paper=self.order_engine.paper_trading
                    )
                    
                    # 4. Daily Telegram Report
                    final_report = format_daily_report(now.strftime("%Y-%m-%d"), "ATM", total_entry_premium, total_exit_premium, trade_stats['net_pnl'], trade_stats['points_captured'])
                    send_telegram_message("🏁 *Market Close Update*\n" + final_report)
                    
                    # 5. Weekly Friday Audit
                    if now.weekday() == 4: # Friday
                        stats = get_weekly_stats()
                        weekly_msg = format_weekly_report(stats)
                        send_telegram_message(weekly_msg)
                    break
                
                time.sleep(10)

    def send_hourly_update(self, now):
        """
        Send status message with P&L and VWAP.
        """
        if not self.active_positions: return
        
        try:
            # 1. Fetch Current Prices
            inst_keys = list(self.active_positions.keys())
            quotes = self.monitor.get_ltp(inst_keys + [self.nifty_key])
            spot = quotes.get(self.nifty_key, 0.0)
            
            # 2. Calculate P&L
            total_entry = sum(pos['entry_price'] for pos in self.active_positions.values() if isinstance(pos['entry_price'], (int, float)))
            total_current = sum(quotes.get(k, pos['entry_price']) for k, pos in self.active_positions.items() if isinstance(quotes.get(k, pos['entry_price']), (int, float)))
            points_gain = total_entry - total_current
            qty = next(iter(self.active_positions.values()))['qty']
            pnl = points_gain * qty
            
            # 3. Calculate VWAP
            vwap = 0.0
            if self.synthetic_premium_history:
                df = pd.DataFrame(self.synthetic_premium_history, columns=['timestamp', 'price', 'volume'])
                vwap = (df['price'] * df['volume']).sum() / df['volume'].sum() if df['volume'].sum() > 0 else total_current
            else:
                vwap = total_current # Fallback
            
            # 4. Send Message
            msg = format_hourly_status(now.strftime("%H:%M"), spot, total_current, pnl, vwap, points_gain)
            send_telegram_message(msg)
            
            # 5. Record History for next VWAP calc
            self.synthetic_premium_history.append((now, total_current, 1)) # Simple volume tracker
            
        except Exception as e:
            logger.error(f"Hourly Update Failed: {str(e)}")

if __name__ == "__main__":
    # Settings derived from config.py
    trader = LiveTrader(paper_trading=PAPER_TRADING)
    trader.run()
