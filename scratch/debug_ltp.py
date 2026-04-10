import sys
import os
sys.path.append(os.getcwd())
import requests
from config import UPSTOX_ACCESS_TOKEN
from live_monitor import LiveMonitor

token = UPSTOX_ACCESS_TOKEN
keys = ["NSE_FO|54810", "NSE_FO|54811", "NSE_INDEX|Nifty 50"]
monitor = LiveMonitor(token)
res = monitor.get_ltp(keys)
print(f"LTP result: {res}")

# Directly check the raw response
url = "https://api.upstox.com/v2/market-quote/ltp"
params = {'instrument_key': ",".join(keys)}
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {token}'
}
response = requests.get(url, headers=headers, params=params)
print(f"Status Code: {response.status_code}")
print(f"Raw Response: {response.text}")
