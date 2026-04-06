# upstox_client.py
import requests
import pandas as pd
import gzip
import io
import os
from datetime import datetime
from config import UPSTOX_ACCESS_TOKEN
from logger import logger

class UpstoxClient:
    def __init__(self, token=UPSTOX_ACCESS_TOKEN):
        self.token = token
        self.base_url = "https://api.upstox.com/v2"
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        self.inst_df = None
        self._ensure_instruments_loaded()

    def get_historical_candles(self, instrument_key, from_date, to_date, interval='1minute'):
        """
        Fetch historical candle data for a given instrument.
        Dates should be in YYYY-MM-DD format.
        """
        url = f"{self.base_url}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        
        try:
            logger.info(f"Fetching historical data for {instrument_key} from {from_date} to {to_date}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'success':
                candles = data['data']['candles']
                # Upstox returns: [timestamp, open, high, low, close, volume, oi]
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Upstox returns data in descending order of time, let's reverse it
                df = df.iloc[::-1].reset_index(drop=True)
                return df
            else:
                logger.error(f"API Error: {data.get('errors')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch data for {instrument_key}: {str(e)}")
            return None

    def _ensure_instruments_loaded(self):
        """
        Download and load the NSE F&O instrument list locally if needed.
        """
        file_path = "NSE_FO.json.gz"
        # Download once a day if missing
        if not os.path.exists(file_path):
            # Using the official assets URL for the NSE JSON master list
            url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
            try:
                logger.info("Downloading official Upstox Instrument List (JSON)...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(response.content)
            except Exception as e:
                logger.error(f"Failed to download instruments: {str(e)}")
                return
        
        try:
            # The JSON file is large, so we load it and filter immediately to save memory
            df = pd.read_json(file_path, compression='gzip')
            # Filter for NSE F&O segment to keep the local search fast
            self.inst_df = df[df['segment'] == 'NSE_FO'].copy()
            logger.info(f"Instrument List Loaded Successfully ({len(self.inst_df)} NSE_FO scrips).")
        except Exception as e:
            logger.error(f"Failed to load instruments into memory: {str(e)}")

    def get_instrument_key(self, trading_symbol):
        """
        Resolve an instrument key from a trading symbol using local search.
        """
        if self.inst_df is None:
            self._ensure_instruments_loaded()
            
        if self.inst_df is not None:
            match = self.inst_df[self.inst_df['trading_symbol'] == trading_symbol]
            if not match.empty:
                return match['instrument_key'].values[0]
        
        logger.error(f"Could not resolve key for {trading_symbol} in local list.")
        return None

    def get_option_symbol(self, strike, expiry_date, type="CE", is_monthly=False):
        """
        Generate the Upstox trading symbol. 
        Weekly: NIFTY2632424000CE
        Monthly: NIFTY26MAR24000CE
        """
        y = expiry_date.strftime("%y")
        if is_monthly:
            m_str = expiry_date.strftime("%b").upper() # MAR, APR, etc.
            symbol = f"NIFTY{y}{m_str}{strike}{type}"
        else:
            m = str(expiry_date.month)
            if m == "10": m = "O"
            elif m == "11": m = "N"
            elif m == "12": m = "D"
            d = expiry_date.strftime("%d")
            symbol = f"NIFTY{y}{m}{d}{strike}{type}"
            
        return symbol

if __name__ == "__main__":
    # Test fetch for Nifty Spot
    client = UpstoxClient()
    # Nifty 50 key: NSE_INDEX|Nifty 50
    df = client.get_historical_candles("NSE_INDEX|Nifty 50", "2026-03-30", "2026-04-02")
    if df is not None:
        print("Fetched Nifty Spot Data:")
        print(df.head())
    else:
        print("Failed to fetch Nifty data. Check token and instrument key.")
