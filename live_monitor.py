# live_monitor.py
import requests
from config import UPSTOX_ACCESS_TOKEN, NIFTY_INST_KEY, VIX_INST_KEY, BROKER
from logger import logger
from alice_blue_helper import AliceBlueClient

class LiveMonitor:
    def __init__(self, token=UPSTOX_ACCESS_TOKEN):
        self.broker = BROKER
        if self.broker == "ALICE_BLUE":
            self.alice_client = AliceBlueClient()
        elif self.broker == "WEBHOOK":
            # For Webhook mode, we still need market data. 
            # Defaulting to Upstox for data sourcing.
            self.token = token
            self.base_url = "https://api.upstox.com/v2"
            self.headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
        else:
            self.token = token
            self.base_url = "https://api.upstox.com/v2"
            self.headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }

    def _get_yahoo_nifty_spot(self):
        """
        Fallback: Fetch Nifty 50 Spot from Yahoo Finance.
        """
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            logger.warning(f"⚠️ Broker API Down. Using Yahoo Finance Fallback for Nifty Spot: {price}")
            return price
        except Exception as e:
            logger.error(f"Yahoo Finance Fallback Failed: {str(e)}")
            return None

    def get_ltp(self, instruments):
        """
        Fetch Last Traded Price (LTP).
        instruments: list of keys (Upstox) or symbols/objects (Alice)
        """
        if not instruments:
            return {}
            
        if self.broker == "ALICE_BLUE":
            res = {}
            for inst in instruments:
                # If inst is string, try to resolve to object
                if isinstance(inst, str):
                    inst_obj = self.alice_client.get_instrument(inst)
                    if inst_obj:
                        val = self.alice_client.get_ltp(inst_obj)
                        res[inst] = val
                else:
                    val = self.alice_client.get_ltp(inst)
                    res[inst['TSymbol']] = val # Map by symbol for consistency
            return res

        # Handle Mock instruments for Paper Trading
        result = {}
        real_instruments = []
        for inst in instruments:
            if isinstance(inst, str) and inst.startswith("MOCK_"):
                result[inst] = 100.0
            else:
                real_instruments.append(inst)

        if not real_instruments:
            return result

        # Upstox implementation
        keys_str = ",".join(real_instruments)
        url = f"{self.base_url}/market-quote/ltp"
        params = {'instrument_key': keys_str}
        
        try:
            from requests import get
            response = get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status', '') == 'success':
                # Map results by both the returned key and the internal instrument_token
                api_data = data.get('data', {})
                if not api_data:
                    logger.warning(f"Upstox API returned success but data is empty for keys: {keys_str}. Are the keys valid?")
                    
                for key, details in api_data.items():
                    price = details.get('last_price')
                    if price is None: 
                        logger.warning(f"Upstox API returned NO 'last_price' for {key}. It may have zero trading volume.")
                        continue
                    
                    # 1. Match by normalization (e.g. NSE_FO:54810 -> NSE_FO|54810)
                    norm_key = key.replace(":", "|")
                    result[norm_key] = price
                    
                    # 2. Match by internal token (e.g. "instrument_token": "NSE_FO|54810")
                    token = details.get('instrument_token')
                    if token:
                        result[token] = price
            else:
                logger.error(f"Upstox API returned non-success status: {data}")
            
            # Check for Nifty Spot Fallback
            if NIFTY_INST_KEY not in result and NIFTY_INST_KEY in instruments:
                yahoo_price = self._get_yahoo_nifty_spot()
                if yahoo_price:
                    result[NIFTY_INST_KEY] = yahoo_price
                    
            return result
        except Exception as e:
            logger.error(f"Failed to fetch LTP: {str(e)}")
            # Even on full crash, try Yahoo fallback if Nifty was requested
            if NIFTY_INST_KEY in instruments:
                yahoo_price = self._get_yahoo_nifty_spot()
                if yahoo_price:
                    return {NIFTY_INST_KEY: yahoo_price}
            return {}

if __name__ == "__main__":
    # Test LTP fetch
    monitor = LiveMonitor()
    res = monitor.get_ltp([NIFTY_INST_KEY, VIX_INST_KEY])
    print(f"LTP Check: {res}")
