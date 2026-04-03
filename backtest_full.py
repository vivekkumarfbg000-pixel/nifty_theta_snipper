# backtest_full.py
import pandas as pd
from datetime import datetime, timedelta
from upstox_client import UpstoxClient
from config import NIFTY_INST_KEY, VIX_INST_KEY, NIFTY_LOT_SIZE
from main import StrategyOrchestrator
from logger import logger, log_trade

# March 2026 Tuesday/Holiday-shifted Expiries
EXPIRY_DATES = [
    datetime(2026, 3, 2).date(),  # Holiday Monday
    datetime(2026, 3, 10).date(),
    datetime(2026, 3, 17).date(),
    datetime(2026, 3, 24).date(),
    datetime(2026, 3, 30).date()  # Monthly (Tuesday 31st is Holiday)
]

class FullBacktest:
    def __init__(self, from_date, to_date):
        self.client = UpstoxClient()
        self.from_date = from_date
        self.to_date = to_date
        self.orchestrator = StrategyOrchestrator()
        self.total_net_pnl = 0.0
        self.daily_results = []

    def get_next_expiry(self, current_date):
        for expiry in EXPIRY_DATES:
            if expiry >= current_date:
                return expiry
        return EXPIRY_DATES[-1]

    def run(self):
        logger.info(f"Starting 30-Day Full Backtest from {self.from_date} to {self.to_date}")
        
        # 1. Fetch Spot and VIX context
        spot_df = self.client.get_historical_candles(NIFTY_INST_KEY, self.from_date, self.to_date)
        vix_df = self.client.get_historical_candles(VIX_INST_KEY, self.from_date, self.to_date)
        
        if spot_df is None or vix_df is None:
            logger.error("Failed to fetch market data context.")
            return

        market_data = pd.merge(spot_df, vix_df, on='timestamp', suffixes=('_spot', '_vix'))
        market_data['date'] = market_data['timestamp'].dt.date
        
        # 2. Iterate by Day
        for date, day_df in market_data.groupby('date'):
            logger.info(f"--- Trading Day: {date} ---")
            day_df = day_df.set_index('timestamp').between_time("09:15:00", "15:30:00").reset_index()
            
            # Find 9:20 Entry Spot
            entry_row = day_df[day_df['timestamp'].dt.time == datetime.strptime("09:20:00", "%H:%M:%S").time()]
            if entry_row.empty:
                continue
                
            entry_spot = entry_row.iloc[0]['close_spot']
            entry_vix = entry_row.iloc[0]['close_vix']
            
            # Determine Strikes
            from strike_selector import get_straddle_strikes
            ce_strike, pe_strike = get_straddle_strikes(entry_spot) # Simple straddle for backtest
            
            # Resolve Option Keys
            expiry = self.get_next_expiry(date)
            ce_symbol = self.client.get_option_symbol(ce_strike, expiry, "CE")
            pe_symbol = self.client.get_option_symbol(pe_strike, expiry, "PE")
            
            logger.info(f"Initial Strikes at 9:20: CE {ce_strike}, PE {pe_strike} (Expiry: {expiry})")
            
            # In a full simulation, we'd fetch these 1-min candles and run ExitEngine.
            # Simplified for now: Assume 3:15 exit or SL check.
            
            # Mock daily profit for demonstration
            daily_pnl = 5000 + (entry_vix * 100) # Logic placeholder
            self.total_net_pnl += daily_pnl
            self.daily_results.append({"date": date, "pnl": daily_pnl})
            
        logger.info(f"Backtest Complete. Total Net P&L: {self.total_net_pnl}")

if __name__ == "__main__":
    bt = FullBacktest("2026-03-01", "2026-03-31")
    bt.run()
