# live_monitor.py
import requests
from config import UPSTOX_ACCESS_TOKEN, NIFTY_INST_KEY, VIX_INST_KEY
from logger import logger

class LiveMonitor:
    def __init__(self, token=UPSTOX_ACCESS_TOKEN):
        self.token = token
        self.base_url = "https://api.upstox.com/v2"
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

    def get_ltp(self, instrument_keys):
        """
        Fetch Last Traded Price (LTP) for a list of instrument keys.
        """
        if not instrument_keys:
            return {}
            
        keys_str = ",".join(instrument_keys)
        url = f"{self.base_url}/market/quote/ltp"
        params = {'symbol': keys_str}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'success':
                result = {}
                for key, details in data['data'].items():
                    result[key] = details['last_price']
                return result
            else:
                logger.error(f"LTP Fetch Error: {data.get('errors')}")
                return {}
        except Exception as e:
            logger.error(f"Failed to fetch LTP: {str(e)}")
            return {}

if __name__ == "__main__":
    # Test LTP fetch
    monitor = LiveMonitor()
    res = monitor.get_ltp([NIFTY_INST_KEY, VIX_INST_KEY])
    print(f"LTP Check: {res}")
