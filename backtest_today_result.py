
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
            return None
        data = r.json()
        candles = data['data']['candles']
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return None

def get_price_at_time(df, time_str, date_str):
    try:
        target_time = datetime.strptime(time_str, "%H:%M").time()
        df_day = df[df['timestamp'].dt.strftime('%Y-%m-%d') == date_str]
        row = df_day[df_day['timestamp'].dt.time == target_time]
        if not row.empty:
            return row['close'].values[0]
        return None
    except:
        return None

# Configuration
TEST_DATE = "2026-04-09"
ENTRY_TIME = "09:20"
EXIT_TIME = "15:15"
EXPIRY = "13 APR 2026"

# ATM Strike at 9:20 AM was 23950 (Spot: 23946.65)
instruments = {
    "CE": {"key": "NSE_FO|54810", "symbol": "NIFTY 23950 CE 13 APR 26"},
    "PE": {"key": "NSE_FO|54811", "symbol": "NIFTY 23950 PE 13 APR 26"}
}

print(f"--- BACKTEST RESULTS: {TEST_DATE} ---")
print(f"Strategy: ATM Straddle (Entry 09:20, Exit 15:15)")
print(f"Strike: 23950 | Expiry: {EXPIRY}\n")

results = {}
for side, info in instruments.items():
    df = fetch_intraday_data(info['key'])
    if df is None:
        print(f"Error: Could not fetch data for {info['symbol']}")
        continue
    
    entry_p = get_price_at_time(df, ENTRY_TIME, TEST_DATE)
    exit_p = get_price_at_time(df, EXIT_TIME, TEST_DATE)
    
    if entry_p is None or exit_p is None:
        # Fallback to nearest available if 15:15 is not reached yet
        if entry_p is not None:
             latest = df[df['timestamp'].dt.strftime('%Y-%m-%d') == TEST_DATE].iloc[0]
             exit_p = latest['close']
             exit_time_actual = latest['timestamp'].strftime("%H:%M")
             print(f"Note: Using latest price at {exit_time_actual} for {side}")
        else:
             print(f"Error: Missing entry data for {info['symbol']}")
             continue
    
    results[side] = {"entry": entry_p, "exit": exit_p, "symbol": info['symbol']}

if len(results) == 2:
    ce, pe = results['CE'], results['PE']
    total_entry = ce['entry'] + pe['entry']
    total_exit = ce['exit'] + pe['exit']
    points = total_entry - total_exit
    gross = points * NIFTY_LOT_SIZE
    
    # Costs (2 lots = 130 qty, but formula uses NIFTY_LOT_SIZE=65?)
    # We use 1 lot (65 qty) for this backtest
    qty = NIFTY_LOT_SIZE
    turnover = (total_entry + total_exit) * qty
    brokerage = BROKERAGE_PER_ORDER * 4
    stt = total_entry * qty * STT_SELL_SIDE_PCT
    trans = turnover * EXCHANGE_TRANSACTION_MODIFIER
    gst = (brokerage + trans) * GST_PCT
    costs = brokerage + stt + trans + gst
    net = gross - costs

    print(f"ENTRY (09:20): {total_entry:.2f} (CE: {ce['entry']} + PE: {pe['entry']})")
    print(f"EXIT  (15:15): {total_exit:.2f} (CE: {ce['exit']} + PE: {pe['exit']})")
    print(f"POINTS: {points:+.2f}")
    print(f"GROSS P&L: ₹{gross:+.2f}")
    print(f"TOTAL COSTS: ₹{costs:.2f}")
    print(f"NET P&L   : ₹{net:+.2f}")
else:
    print("Backtest failed due to missing data.")
