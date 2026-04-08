
from upstox_helper import UpstoxClient
from datetime import datetime
import pandas as pd

client = UpstoxClient()
yesterday = "2026-04-07"
spot_key = "NSE_INDEX|Nifty 50"

print(f"Fetching HISTORICAL spot data for {spot_key} on {yesterday}...")
df = client.get_historical_candles(spot_key, yesterday, yesterday)

if df is not None:
    # Filter for Nifty Spot
    target_time = datetime.strptime("09:20:00", "%H:%M:%S").time()
    df['time'] = df['timestamp'].dt.time
    match = df[df['time'] == target_time]
    
    if not match.empty:
        spot_price = match.iloc[0]['close']
        print(f"Nifty Spot at 09:20 on {yesterday}: {spot_price}")
        atm = int(round(spot_price / 50) * 50)
        print(f"ATM Strike: {atm}")
    else:
        print(f"9:20 candle not found for {yesterday}.")
        if not df.empty:
            print(f"Available times: {df['timestamp'].min()} to {df['timestamp'].max()}")
else:
    print("Failed to fetch historical data.")
