import pandas as pd
from datetime import datetime
from logger import logger
from upstox_helper import UpstoxClient

# Nifty 50 Expiry Rules:
# Pre-Sep 2025: Thursdays
# Post-Sep 2025: Tuesdays

def get_nifty_expiries_2025_2026():
    """
    Generate a list of Nifty weekly/monthly expiry dates for the backtest range.
    (This list accounts for the Thursday-to-Tuesday transition and holidays).
    """
    # Thursdays (Apr 2025 - Aug 2025)
    thursdays = [
        "2025-04-03", "2025-04-10", "2025-04-17", "2025-04-24",
        "2025-05-01", "2025-05-08", "2025-05-15", "2025-05-22", "2025-05-29",
        "2025-06-05", "2025-06-12", "2025-06-19", "2025-06-26",
        "2025-07-03", "2025-07-10", "2025-07-17", "2025-07-24", "2025-07-31",
        "2025-08-07", "2025-08-14", "2025-08-21", "2025-08-28"
    ]
    # Tuesdays (Sep 2025 - Apr 2026)
    tuesdays = [
        "2025-09-02", "2025-09-09", "2025-09-16", "2025-09-23", "2025-09-30",
        "2025-10-07", "2025-10-14", "2025-10-21", "2025-10-28",
        "2025-11-04", "2025-11-11", "2025-11-18", "2025-11-25",
        "2025-12-02", "2025-12-09", "2025-12-16", "2025-12-23", "2025-12-30",
        "2026-01-06", "2026-01-13", "2026-01-20", "2026-01-27",
        "2026-02-03", "2026-02-10", "2026-02-17", "2026-02-24",
        "2026-03-02", "2026-03-10", "2026-03-17", "2026-03-24", "2026-03-30",
        "2026-04-07", "2026-04-13", "2026-04-21", "2026-04-28"
    ]
    all_expiries = [datetime.strptime(d, "%Y-%m-%d").date() for d in thursdays + tuesdays]
    return all_expiries

class VWAPBacktester:
    def __init__(self, from_date, to_date):
        self.client = UpstoxClient()
        self.from_date = from_date
        self.to_date = to_date
        self.expiry_calendar = get_nifty_expiries_2025_2026()

    def get_next_expiry(self, current_date):
        for expiry in self.expiry_calendar:
            if expiry >= current_date:
                return expiry
        return self.expiry_calendar[-1]

    def calculate_vwap(self, df):
        df['pv'] = df['price'] * df['volume']
        df['cum_pv'] = df['pv'].cumsum()
        df['cum_vol'] = df['volume'].cumsum()
        df['vwap'] = df['cum_pv'] / df['cum_vol']
        return df

    def fetch_day_data(self, date_obj):
        """
        Fetch 1-minute data for Nifty Spot and ATM legs from Upstox.
        """
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # 1. Fetch Nifty Spot for 9:20 Entry Strike selection
        spot_df = self.client.get_historical_candles("NSE_INDEX|Nifty 50", date_str, date_str)
        if spot_df is None or spot_df.empty: return None
        
        # Filter for 09:20
        # Upstox timestamps are often local
        spot_df['time'] = spot_df['timestamp'].dt.time
        entry_row = spot_df[spot_df['time'] == datetime.strptime("09:20:00", "%H:%M:%S").time()]
        if entry_row.empty: return None
        
        spot = entry_row.iloc[0]['close']
        strike = round(spot / 50) * 50
        
        # 2. Get Instrument Keys
        expiry = self.get_next_expiry(date_obj)
        # Simple monthly check: Last Tuesday of month
        is_monthly = (expiry.day > 24) and (expiry.month == date_obj.month)
        
        ce_sym = self.client.get_option_symbol(strike, expiry, "CE", is_monthly)
        pe_sym = self.client.get_option_symbol(strike, expiry, "PE", is_monthly)
        
        ce_key = self.client.get_instrument_key(ce_sym)
        pe_key = self.client.get_instrument_key(pe_sym)
        
        if not ce_key or not pe_key: return None
        
        # 3. Fetch 1m Candles for Legs
        ce_df = self.client.get_historical_candles(ce_key, date_str, date_str)
        pe_df = self.client.get_historical_candles(pe_key, date_str, date_str)
        
        if ce_df is None or pe_df is None: return None
        
        # Combine into Synthetic Premium
        df = pd.merge(ce_df[['timestamp', 'close', 'volume']], pe_df[['timestamp', 'close', 'volume']], on='timestamp', suffixes=('_ce', '_pe'))
        df['price'] = df['close_ce'] + df['close_pe']
        df['volume'] = df['volume_ce'] + df['volume_pe']
        df = self.calculate_vwap(df)
        
        return df, strike

    def run_real_audit(self):
        logger.info(f"--- STARTING REAL-DATA AUDIT (APRIL 02, 2026) ---")
        
        audit_dates = [datetime(2026, 4, 2).date()]
        total_pnl = 0
        
        print("\n" + "="*85)
        print(f"{'Date':<12} | {'Strike':<8} | {'Entry (9:20)':<12} | {'Exit Price':<12} | {'P&L (₹)'}")
        print("-" * 85)
        
        for d in audit_dates:
            result = self.fetch_day_data(d)
            if result:
                df, strike = result
                # V3 Performance Simulation on Actual Data
                entry_price = df.iloc[0]['price']
                exit_price = df.iloc[-1]['price'] # EOD exit for simplicity in audit
                pnl = (entry_price - exit_price) * 100 # 2 lots
                total_pnl += pnl
                print(f"{d.strftime('%Y-%m-%d'):<12} | {strike:<8} | {entry_price:<12.2f} | {exit_price:<12.2f} | {pnl:>9,.2f}")
            else:
                print(f"{d.strftime('%Y-%m-%d'):<12} | FAILED TO RESOLVE DATA")
                
        print("-" * 85)
        print(f"TOTAL REAL-DATA AUDIT P&L: ₹{total_pnl:,.2f}")
        print("="*85)

if __name__ == "__main__":
    tester = VWAPBacktester("2025-04-01", "2026-03-31")
    tester.run_real_audit()
