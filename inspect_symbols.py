import pandas as pd
import gzip
import json

file_path = "c:/Users/vivek/OneDrive/Desktop/OneDrive/Documents/nifty_theta_sniper/NSE_FO.json.gz"
try:
    df = pd.read_json(file_path, compression='gzip')
    nifty_fo = df[df['trading_symbol'].str.contains("NIFTY26", na=False)]
    print(nifty_fo[['trading_symbol', 'instrument_key']].head(20))
except Exception as e:
    print(f"Error: {e}")
