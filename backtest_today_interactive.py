
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from config import NIFTY_LOT_SIZE, STT_SELL_SIDE_PCT, BROKERAGE_PER_ORDER, GST_PCT, EXCHANGE_TRANSACTION_MODIFIER

load_dotenv()
token = os.getenv('UPSTOX_ACCESS_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def fetch_intraday_data(key):
    try:
        url = f'https://api.upstox.com/v2/historical-candle/intraday/{key}/1minute'
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"Error fetching data for {key}: {r.status_code}")
            return None
        data = r.json()
        candles = data['data']['candles']
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"Exception for {key}: {str(e)}")
        return None

def get_price_at_time(df, time_str, date_str):
    try:
        target_time = datetime.strptime(time_str, "%H:%M").time()
        # Filter for the specific day
        df_day = df[df['timestamp'].dt.strftime('%Y-%m-%d') == date_str]
        row = df_day[df_day['timestamp'].dt.time == target_time]
        if not row.empty:
            return row['close'].values[0]
        return None
    except:
        return None

# Configuration for Backtest
today = "2026-04-08"
entry_time = "09:20"
exit_time = "15:15"
expiry = "13 APR 2026"
lot_size = NIFTY_LOT_SIZE

instruments = {
    "CE": {"key": "NSE_FO|54808", "symbol": "NIFTY 23900 CE 13 APR 26"},
    "PE": {"key": "NSE_FO|54809", "symbol": "NIFTY 23900 PE 13 APR 26"}
}

print(f"--- BACKTEST: NIFTY STRADDLE (ATM 23900) ---")
print(f"Date: {today} | Entry: {entry_time} | Exit: {exit_time} | Expiry: {expiry}")
print(f"Lot Size: {lot_size}\n")

results = {}
for side, info in instruments.items():
    print(f"Fetching data for {info['symbol']}...")
    df = fetch_intraday_data(info['key'])
    if df is None:
        print(f"Failed to fetch data for {info['symbol']}")
        continue
    
    entry_p = get_price_at_time(df, entry_time, today)
    exit_p = get_price_at_time(df, exit_time, today)
    
    if entry_p is None or exit_p is None:
        print(f"Could not find entry/exit prices for {info['symbol']}")
        # Try to show available times
        df_today = df[df['timestamp'].dt.strftime('%Y-%m-%d') == today]
        if not df_today.empty:
            print(f"Data available from {df_today['timestamp'].min()} to {df_today['timestamp'].max()}")
        continue
    
    results[side] = {"entry": entry_p, "exit": exit_p, "symbol": info['symbol']}

if len(results) == 2:
    ce = results['CE']
    pe = results['PE']
    
    total_entry = ce['entry'] + pe['entry']
    total_exit = ce['exit'] + pe['exit']
    points_pnl = total_entry - total_exit # Shorting
    gross_pnl = points_pnl * lot_size
    
    print("\n[TRADE DETAILS]")
    print(f" - CE Entry: {ce['entry']} | PE Entry: {pe['entry']} (Total: {total_entry:.2f})")
    print(f" - CE Exit:  {ce['exit']} | PE Exit:  {pe['exit']} (Total: {total_exit:.2f})")
    print(f" - Points Gained: {points_pnl:.2f}")
    print(f" - Gross P&L: ₹{gross_pnl:.2f}")
    
    # Cost Calculation
    # Turnover = (Total Entry + Total Exit) * Lot Size
    turnover = (total_entry + total_exit) * lot_size
    brokerage = BROKERAGE_PER_ORDER * 4 # 2 Entry + 2 Exit
    stt = total_entry * lot_size * STT_SELL_SIDE_PCT # STT only on sell side (entry for shorting)
    trans_charges = turnover * EXCHANGE_TRANSACTION_MODIFIER
    gst = (brokerage + trans_charges) * GST_PCT
    total_costs = brokerage + stt + trans_charges + gst
    net_pnl = gross_pnl - total_costs
    
    print("\n[COSTS & NET]")
    print(f" - Brokerage: ₹{brokerage:.2f}")
    print(f" - STT (0.15% on Sell): ₹{stt:.2f}")
    print(f" - Trans Charges: ₹{trans_charges:.2f}")
    print(f" - GST (18% on B+T): ₹{gst:.2f}")
    print(f" - Total Costs: ₹{total_costs:.2f}")
    print(f" - NET P&L: ₹{net_pnl:.2f}")
    
    if net_pnl > 0:
        print("\nRESULT: SUCCESS (PROFIT)")
    else:
        print("\nRESULT: FAILURE (LOSS)")

else:
    print("\nError: Could not complete backtest due to missing data.")
