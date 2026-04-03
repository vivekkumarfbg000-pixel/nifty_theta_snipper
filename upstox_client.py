# upstox_client.py
import requests
import pandas as pd
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

    def get_instrument_key(self, trading_symbol):
        """
        Resolve an instrument key from a trading symbol using the Search API.
        """
        url = "https://api.upstox.com/v1/instruments/search"
        params = {'query': trading_symbol, 'segments': 'FO'}
        
        try:
            # We use the same headers (token is valid for v1 and v2)
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'success':
                for item in data['data']:
                    # Exact match check
                    if item['trading_symbol'] == trading_symbol:
                        return item['instrument_key']
            return None
        except Exception as e:
            logger.error(f"Failed to resolve key for {trading_symbol}: {str(e)}")
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
