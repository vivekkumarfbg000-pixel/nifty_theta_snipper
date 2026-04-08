import pandas as pd
import gzip
import io
import os

file_path = "NSE_FO.json.gz"
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found!")
    exit(1)

try:
    df = pd.read_json(file_path, compression='gzip')
    print(f"Total rows: {len(df)}")
    print(f"Segments: {df['segment'].unique()}")
    
    nifty_df = df[df['name'].str.contains('NIFTY', case=False, na=False)]
    print(f"NIFTY rows: {len(nifty_df)}")
    
    if not nifty_df.empty:
        print("\nSample NIFTY 50 Rows:")
        # Some versions use 'NIFTY 50' as the name
        print(nifty_df[nifty_df['name'].isin(['NIFTY', 'NIFTY 50'])].head(10))
        
        print("\nUnique Names in NIFTY match:")
        print(nifty_df['name'].unique())
        
        print("\nCheck for April 9, 2026 expiry:")
        df['expiry_dt_str'] = pd.to_datetime(df['expiry'], unit='ms', errors='coerce').dt.date.astype(str)
        expiry_nifty = nifty_df[pd.to_datetime(nifty_df['expiry'], unit='ms', errors='coerce').dt.date.astype(str) == '2026-04-09']
        print(f"NIFTY rows on 2026-04-09: {len(expiry_nifty)}")
except Exception as e:
    print(f"Failed to read file: {e}")
