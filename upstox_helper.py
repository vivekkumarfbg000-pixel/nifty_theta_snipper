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

    def get_instrument_key(self, strike=None, expiry_date=None, option_type=None, trading_symbol=None):
        """
        Resolve an instrument key. 
        Highly robust: Searches by Strike/Expiry/Type if provided, falls back to trading_symbol.
        """
        if self.inst_df is None:
            self._ensure_instruments_loaded()
            
        if self.inst_df is not None:
            if strike is not None and expiry_date is not None and option_type is not None:
                # 1. Search by attributes (Robust)
                # Convert expiry to YYYY-MM-DD if it's a datetime object
                if isinstance(expiry_date, datetime):
                    expiry_str = expiry_date.strftime("%Y-%m-%d")
                else:
                    expiry_str = expiry_date
                
                # Check for various common Upstox JSON column names
                def get_col(candidates):
                    for c in candidates:
                        if c in self.inst_df.columns: return f"['{c}']"
                        # Case insensitive search
                        for col in self.inst_df.columns:
                            if c.lower() == col.lower(): return f"['{col}']"
                    return None

                strike_col = 'strike_price' if 'strike_price' in self.inst_df.columns else 'strike'
                expiry_col = 'expiry' if 'expiry' in self.inst_df.columns else None
                type_col = 'instrument_type' if 'instrument_type' in self.inst_df.columns else 'option_type'
                
                if not expiry_col:
                    cols = [c for c in self.inst_df.columns if 'expiry' in c.lower()]
                    if cols: expiry_col = cols[0]

                if strike_col in self.inst_df.columns and expiry_col and type_col in self.inst_df.columns:
                    # 1. Ensure columns are processed correctly (numeric strike, date-string expiry)
                    self.inst_df[strike_col] = pd.to_numeric(self.inst_df[strike_col], errors='coerce')
                    
                    # Robust Expiry conversion: handles Unix ms, Unix s, and standard strings
                    if pd.api.types.is_numeric_dtype(self.inst_df[expiry_col]):
                        # 1.7e12 is definitely milliseconds
                        self.inst_df['expiry_dt_str'] = pd.to_datetime(self.inst_df[expiry_col], unit='ms', errors='coerce').dt.date.astype(str)
                    else:
                        self.inst_df['expiry_dt_str'] = pd.to_datetime(self.inst_df[expiry_col], errors='coerce').dt.date.astype(str)
                    
                    matches = self.inst_df[
                        (self.inst_df[strike_col] == float(strike)) & 
                        (self.inst_df['expiry_dt_str'] == expiry_str) &
                        (self.inst_df[type_col].str.upper() == option_type.upper()) &
                        (self.inst_df['name'].str.contains("NIFTY", case=False))
                    ].copy()
                    
                    if not matches.empty:
                        # Priority: exact 'NIFTY' or 'NIFTY 50' name
                        nifty_match = matches[matches['name'].isin(['NIFTY', 'NIFTY 50'])]
                        if nifty_match.empty: nifty_match = matches # Fallback
                        
                        key = nifty_match['instrument_key'].values[0]
                        symbol = nifty_match['trading_symbol'].values[0]
                        logger.info(f"SUCCESS: Resolved {symbol} -> {key}")
                        return key, symbol

            # 2. Fallback to trading_symbol search
            if trading_symbol:
                match = self.inst_df[self.inst_df['trading_symbol'] == trading_symbol]
                if not match.empty:
                    return match['instrument_key'].values[0], trading_symbol
        
        logger.error(f"Could not resolve key for {trading_symbol or strike} in local list.")
        return None, None

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
