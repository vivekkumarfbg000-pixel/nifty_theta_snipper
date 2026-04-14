
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from config import NIFTY_LOT_SIZE, STT_SELL_SIDE_PCT, BROKERAGE_PER_ORDER, GST_PCT, EXCHANGE_TRANSACTION_MODIFIER

load_dotenv()
token = os.getenv('UPSTOX_ACCESS_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def fetch_intraday_data(key, symbol):
    try:
        url = f'https://api.upstox.com/v2/historical-candle/intraday/{key}/1minute'
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        candles = data['data']['candles']
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    except:
        return None

# Configuration
DATE_STR = "2026-04-10"
ENTRY_TIME = "09:20"
EXIT_TIME = "15:15"
STOP_LOSS_PCT = 0.25
LOT_SIZE = NIFTY_LOT_SIZE

instruments = {
    "CE": {"key": "NSE_FO|54810", "symbol": "NIFTY 23950 CE 13 APR 26"},
    "PE": {"key": "NSE_FO|54811", "symbol": "NIFTY 23950 PE 13 APR 26"}
}

print(f"=== BACKTEST: 9:20 STRADDLE (ATM 23950) ===")
print(f"Date: {DATE_STR} | SL: {STOP_LOSS_PCT*100}% | Exit: {EXIT_TIME}\n")

results = {}
for side, info in instruments.items():
    df = fetch_intraday_data(info['key'], info['symbol'])
    if df is None:
        print(f"Failed to fetch data for {side}")
        continue
    
    # Filter for today
    df['time_str'] = df['timestamp'].dt.strftime('%H:%M')
    df_today = df[df['timestamp'].dt.strftime('%Y-%m-%d') == DATE_STR].copy()
    
    if df_today.empty:
        print(f"No data for {DATE_STR} for {side}")
        continue
    
    # Find Entry Price
    entry_row = df_today[df_today['time_str'] == ENTRY_TIME]
    if entry_row.empty:
        print(f"Could not find {ENTRY_TIME} candle for {side}")
        continue
    
    entry_price = entry_row.iloc[0]['close']
    entry_ts = entry_row.iloc[0]['timestamp']
    sl_price = entry_price * (1 + STOP_LOSS_PCT)
    
    # Trade data (after entry)
    trade_df = df_today[df_today['timestamp'] > entry_ts].copy()
    
    exit_price = None
    exit_reason = "Time Exit"
    exit_time = None
    
    for _, row in trade_df.iterrows():
        # Check SL
        if row['high'] >= sl_price:
            exit_price = sl_price
            exit_time = row['timestamp']
            exit_reason = f"SL Hit @ {row['time_str']}"
            break
        
        # Check Time Exit
        if row['time_str'] >= EXIT_TIME:
            exit_price = row['close']
            exit_time = row['timestamp']
            exit_reason = "Time Exit"
            break
            
    if exit_price is None:
        if not trade_df.empty:
            exit_price = trade_df.iloc[-1]['close']
            exit_time = trade_df.iloc[-1]['timestamp']
            exit_reason = "End of available data"
        else:
            print(f"No trade data after entry for {side}")
            continue

    results[side] = {
        "symbol": info['symbol'],
        "entry": entry_price,
        "sl": sl_price,
        "exit": exit_price,
        "exit_time": exit_time,
        "reason": exit_reason,
        "pnl_pts": entry_price - exit_price
    }

if len(results) == 2:
    print("\n" + "="*70)
    print(f"{'Side':<5} | {'Entry':<8} | {'SL':<8} | {'Exit':<8} | {'PnL Pts':<10} | {'Reason'}")
    print("-" * 70)
    total_pnl_pts = 0
    for side in ["CE", "PE"]:
        r = results[side]
        print(f"{side:<5} | {r['entry']:<8.2f} | {r['sl']:<8.2f} | {r['exit']:<8.2f} | {r['pnl_pts']:<10.2f} | {r['reason']}")
        total_pnl_pts += r['pnl_pts']
    
    gross_pnl = total_pnl_pts * LOT_SIZE
    print("-" * 70)
    print(f"COMBINED PNL POINTS: {total_pnl_pts:.2f}")
    print(f"GROSS PNL: INR {gross_pnl:.2f}")
    
    # Cost calculation
    total_entry = results['CE']['entry'] + results['PE']['entry']
    total_exit = results['CE']['exit'] + results['PE']['exit']
    turnover = (total_entry + total_exit) * LOT_SIZE
    brokerage = BROKERAGE_PER_ORDER * 4
    stt = total_entry * LOT_SIZE * STT_SELL_SIDE_PCT
    trans_charges = turnover * EXCHANGE_TRANSACTION_MODIFIER
    gst = (brokerage + trans_charges) * GST_PCT
    total_costs = brokerage + stt + trans_charges + gst
    net_pnl = gross_pnl - total_costs
    
    print("\n[COST ANALYSIS]")
    print(f" - Brokerage: INR {brokerage:.2f}")
    print(f" - STT (Sell Side): INR {stt:.2f}")
    print(f" - Trans Charges: INR {trans_charges:.2f}")
    print(f" - GST: INR {gst:.2f}")
    print(f" - Total Costs: INR {total_costs:.2f}")
    print("\nNET PNL: INR {:.2f}".format(net_pnl))
    
    if net_pnl > 0:
        print("\nRESULT: SUCCESS (PROFIT)")
    else:
        print("\nRESULT: FAILURE (LOSS)")
else:
    print("\nERROR: Backtest incomplete.")
