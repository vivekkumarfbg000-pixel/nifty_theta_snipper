
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

# Nifty Spot for 9:20
spot_key = "NSE_INDEX|Nifty 50"
df_spot = fetch_intraday_data(spot_key)
if df_spot is not None:
    today_str = "2026-04-10"
    df_today = df_spot[df_spot['timestamp'].dt.strftime('%Y-%m-%d') == today_str]
    target_time = datetime.strptime("09:20", "%H:%M").time()
    row = df_today[df_today['timestamp'].dt.time == target_time]
    if not row.empty:
        spot_price = row.iloc[0]['close']
        print(f"NIFTY_SPOT_920: {spot_price}")
        atm = int(round(spot_price / 50) * 50)
        print(f"ATM_STRIKE: {atm}")
    else:
        print("SPOT_ERROR: 9:20 candle not found")

# Expiries and Instruments
df_inst = pd.read_json('NSE_FO.json.gz', compression='gzip')
nifty_inst = df_inst[df_inst['name'].str.upper().isin(['NIFTY', 'NIFTY 50'])].copy()
# Handle numeric expiry (ms timestamp)
nifty_inst['expiry_dt'] = pd.to_datetime(nifty_inst['expiry'], unit='ms', errors='coerce')

today = datetime(2026, 4, 10).date()
expiries = sorted(nifty_inst['expiry_dt'].dropna().unique())
future_expiries = [e for e in expiries if e.date() >= today]

print("\nEXPIRIES:")
for e in future_expiries[:5]:
    print(e.strftime('%Y-%m-%d'))

# Find target instruments
if 'atm' in locals():
    target_expiry = future_expiries[0] # Assume nearest
    print(f"\nTARGET_EXPIRY: {target_expiry.strftime('%Y-%m-%d')}")
    
    # Filter for strike and expiry
    # Note: strike might be in floats or ints in the JSON
    strike_col = 'strike_price' if 'strike_price' in df_inst.columns else 'strike'
    nifty_inst[strike_col] = pd.to_numeric(nifty_inst[strike_col], errors='coerce')
    
    matches = nifty_inst[
        (nifty_inst[strike_col] == float(atm)) & 
        (nifty_inst['expiry_dt'].dt.date == target_expiry.date())
    ]
    
    print("\nMATCHING_INSTRUMENTS:")
    for _, row in matches.iterrows():
        print(f"{row['instrument_type']} | {row['trading_symbol']} | {row['instrument_key']}")
