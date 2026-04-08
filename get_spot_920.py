
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
token = os.getenv('UPSTOX_ACCESS_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def fetch_intraday_data(key):
    try:
        url = f'https://api.upstox.com/v2/historical-candle/intraday/{key}/1minute'
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        candles = data['data']['candles']
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return None

today = "2026-04-08"
spot_key = "NSE_INDEX|Nifty 50"

print(f"Fetching INTRADAY spot data for {spot_key}...")
df = fetch_intraday_data(spot_key)

if df is not None:
    # Filter for today
    df_today = df[df['timestamp'].dt.strftime('%Y-%m-%d') == today]
    if df_today.empty:
        print(f"No intraday data found for {today}. Times available:")
        print(df['timestamp'].head(1))
        print(df['timestamp'].tail(1))
    else:
        # Filter for 9:20
        target_time = datetime.strptime("09:20:00", "%H:%M:%S").time()
        match = df_today[df_today['timestamp'].dt.time == target_time]
        if not match.empty:
            spot_price = match.iloc[0]['close']
            print(f"Nifty Spot at 09:20: {spot_price}")
            atm = int(round(spot_price / 50) * 50)
            print(f"ATM Strike: {atm}")
        else:
            print("9:20 candle not found in intraday data.")
else:
    print("Failed to fetch intraday spot data.")
