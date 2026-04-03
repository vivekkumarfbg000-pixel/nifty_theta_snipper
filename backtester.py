# backtester.py
import pandas as pd
from datetime import datetime, timedelta
from main import StrategyOrchestrator
from upstox_client import UpstoxClient
from config import NIFTY_INST_KEY, VIX_INST_KEY
from logger import logger

class HistoricalBacktester:
    def __init__(self, from_date, to_date):
        self.client = UpstoxClient()
        self.from_date = from_date
        self.to_date = to_date
        self.orchestrator = StrategyOrchestrator()
        
    def fetch_market_context(self):
        """
        Fetch Nifty Spot and VIX data for the entire backtest range.
        """
        self.spot_df = self.client.get_historical_candles(NIFTY_INST_KEY, self.from_date, self.to_date)
        self.vix_df = self.client.get_historical_candles(VIX_INST_KEY, self.from_date, self.to_date)
        
        if self.spot_df is None or self.vix_df is None:
            raise Exception("Failed to fetch market context (Spot/VIX)")
        
        # Merge on timestamp
        self.market_data = pd.merge(self.spot_df, self.vix_df, on='timestamp', suffixes=('_spot', '_vix'))
        # Group by date for easier iteration
        self.market_data['date'] = self.market_data['timestamp'].dt.date
        self.daily_groups = self.market_data.groupby('date')

    def run(self):
        logger.info(f"Starting Historical Backtest from {self.from_date} to {self.to_date}")
        self.fetch_market_context()
        
        for date, day_df in self.daily_groups:
            logger.info(f"Processing day: {date}")
            # Filter for trading hours (9:15 to 3:30)
            day_df = day_df.set_index('timestamp').between_time("09:15:00", "15:30:00").reset_index()
            
            if day_df.empty:
                continue
                
            # Here we'd integrate the option price fetching for the 9:20 strikes.
            # 1. At 9:20, identify strikes from day_df.loc[day_df.timestamp.dt.time == 09:20]
            # 2. Fetch those strikes' historical candles for the day.
            # 3. Simulate orchestrator.run_day
            
            # Simple simulation for now to show the flow
            for _, row in day_df.iterrows():
                curr_time_str = row['timestamp'].strftime("%H:%M:%S")
                spot = row['close_spot']
                vix = row['close_vix']
                adx = 20 # Mock ADX for now
                
                self.orchestrator.run_day(
                    lambda: spot,
                    lambda: vix,
                    lambda: adx,
                    curr_time_str
                )
        
        logger.info("Historical Backtest Complete.")

if __name__ == "__main__":
    # Test for 1 day
    bt = HistoricalBacktester("2026-03-31", "2026-04-02")
    bt.run()
