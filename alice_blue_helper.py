# alice_blue_helper.py
import os
import pandas as pd
import pyotp
from pya3 import Aliceblue
from datetime import datetime
from config import ALICE_BLUE_USER_ID, ALICE_BLUE_API_KEY, ALICE_BLUE_API_SECRET, ALICE_BLUE_TOTP_KEY
from logger import logger

class AliceBlueClient:
    def __init__(self):
        self.user_id = ALICE_BLUE_USER_ID
        self.api_key = ALICE_BLUE_API_KEY
        self.api_secret = ALICE_BLUE_API_SECRET
        self.totp_key = ALICE_BLUE_TOTP_KEY
        self.session_id = None
        self.alice = None
        self.inst_df = None
        
        if self.user_id and self.api_key:
            self._login()
            self._ensure_instruments_loaded()
        else:
            logger.error("Alice Blue credentials not found in environment.")

    def _login(self):
        """
        Authenticate with Alice Blue using TOTP.
        """
        try:
            logger.info(f"Attempting Alice Blue login for {self.user_id}...")
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_key).now()
            
            # Initialize Aliceblue Object
            self.alice = Aliceblue(
                user_id=self.user_id,
                api_key=self.api_key,
                totp=totp
            )
            
            # Get Session ID
            self.session_id = self.alice.get_session_id()
            if self.session_id and 'sessionID' in self.session_id:
                logger.info("Alice Blue Login Successful.")
            else:
                logger.error(f"Alice Blue Login Failed: {self.session_id}")
                
        except Exception as e:
            logger.error(f"Alice Blue Authentication Error: {str(e)}")

    def _ensure_instruments_loaded(self):
        """
        Load Alice Blue master contracts.
        """
        try:
            logger.info("Loading Alice Blue Master Contracts...")
            # pya3 handles fetching and caching internally, but we can store locally if needed
            # For now, we'll keep it simple and use the built-in search
            pass
        except Exception as e:
            logger.error(f"Failed to load Alice Blue instruments: {str(e)}")

    def get_historical_candles(self, instrument, from_date, to_date, interval='1'):
        """
        Fetch historical candle data.
        interval: '1', 'D', etc.
        """
        try:
            # from_date, to_date should be datetime objects
            if isinstance(from_date, str):
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
            if isinstance(to_date, str):
                to_date = datetime.strptime(to_date, "%Y-%m-%d")
                
            data = self.alice.get_historical(instrument, from_date, to_date, interval)
            if data and isinstance(data, list):
                df = pd.DataFrame(data)
                # Normalize columns to match system expected format
                # Alice Blue returns: {'datetime': ..., 'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ...}
                df.rename(columns={'datetime': 'timestamp'}, inplace=True)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            return None
        except Exception as e:
            logger.error(f"Error fetching Alice Blue historical data: {str(e)}")
            return None

    def get_instrument(self, symbol, exchange='NFO'):
        """
        Search for an instrument by symbol.
        """
        try:
            return self.alice.get_instrument_by_symbol(exchange, symbol)
        except Exception as e:
            logger.error(f"Error resolving symbol {symbol} on {exchange}: {str(e)}")
            return None

    def get_ltp(self, instrument):
        """
        Get Last Traded Price for an instrument.
        """
        try:
            res = self.alice.get_scrip_info(instrument)
            if res and 'Ltp' in res:
                return float(res['Ltp'])
            return None
        except Exception as e:
            logger.error(f"Error getting LTP: {str(e)}")
            return None

    def get_option_symbol(self, strike, expiry_date, type="CE", is_monthly=False):
        """
        Generate the Alice Blue trading symbol.
        Format: NIFTY 23rd APR 18000 CE (Example)
        Actually, pya3 helper methods are better for this.
        """
        # For Alice Blue, symbols are typically like 'NIFTY24APR19000CE'
        # We can use the AliceBlue.get_instrument_for_fno
        pass

if __name__ == "__main__":
    # Test stub
    client = AliceBlueClient()
    if client.session_id:
        print("Logged in!")
