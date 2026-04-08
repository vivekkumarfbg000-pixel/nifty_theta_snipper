
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from config import NIFTY_LOT_SIZE, STT_SELL_SIDE_PCT, BROKERAGE_PER_ORDER, GST_PCT, EXCHANGE_TRANSACTION_MODIFIER
from upstox_helper import UpstoxClient

def get_price_at_time(df, time_str):
    try:
        target_time = datetime.strptime(time_str, "%H:%M").time()
        df['time'] = df['timestamp'].dt.time
        match = df[df['time'] == target_time]
        if not match.empty:
            return match.iloc[0]['close']
        return None
    except:
        return None

# Configuration
date_str = "2026-04-07"
entry_time = "09:20"
exit_time = "15:15"
lot_size = NIFTY_LOT_SIZE

client = UpstoxClient()

instruments = {
    "CE": {"key": "NSE_FO|54755", "symbol": "NIFTY 22750 CE 13 APR 26"},
    "PE": {"key": "NSE_FO|54756", "symbol": "NIFTY 22750 PE 13 APR 26"}
}

print(f"--- BACKTEST: YESTERDAY NIFTY STRADDLE (ATM 22750) ---")
print(f"Date: {date_str} | Entry: {entry_time} | Exit: {exit_time}")
print(f"Lot Size: {lot_size}\n")

results = {}
for side, info in instruments.items():
    print(f"Fetching historical data for {info['symbol']}...")
    df = client.get_historical_candles(info['key'], date_str, date_str)
    if df is None or df.empty:
        print(f"Failed to fetch data for {info['symbol']}")
        continue
    
    entry_p = get_price_at_time(df, entry_time)
    exit_p = get_price_at_time(df, exit_time)
    
    if entry_p is None or exit_p is None:
        print(f"Could not find entry/exit prices for {info['symbol']}")
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
    turnover = (total_entry + total_exit) * lot_size
    brokerage = BROKERAGE_PER_ORDER * 4
    stt = total_entry * lot_size * STT_SELL_SIDE_PCT
    trans_charges = turnover * EXCHANGE_TRANSACTION_MODIFIER
    gst = (brokerage + trans_charges) * GST_PCT
    total_costs = brokerage + stt + trans_charges + gst
    net_pnl = gross_pnl - total_costs
    
    print("\n[COSTS & NET]")
    print(f" - Total Costs: ₹{total_costs:.2f}")
    print(f" - NET P&L: ₹{net_pnl:.2f}")
    
    if net_pnl > 0:
        print("\nRESULT: SUCCESS (PROFIT)")
    else:
        print("\nRESULT: FAILURE (LOSS)")
else:
    print("\nError: Missing data for backtest.")
