import pandas as pd
import gzip
import os

file_path = "NSE_FO.json.gz"
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found!")
else:
    try:
        print("--- Upstox Instrument List Inspection ---")
        df = pd.read_json(file_path, compression='gzip')
        print(f"Total rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Look for NIFTY
        nifty = df[df['name'].str.contains("NIFTY", na=False, case=False)].head(5)
        if not nifty.empty:
            print("\nSample NIFTY rows:")
            print(nifty[['instrument_key', 'trading_symbol', 'name', 'expiry', 'strike_price' if 'strike_price' in df.columns else 'strike']])
        else:
            print("\nNo NIFTY rows found!")
            
        # Check segment
        print(f"\nSegments found: {df['segment'].unique().tolist()}")
        
    except Exception as e:
        print(f"Error reading file: {e}")
