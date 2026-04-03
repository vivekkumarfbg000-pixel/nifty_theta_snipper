# trade_journal.py
import os
import pandas as pd
from datetime import datetime
from config import TRADES_CSV_PATH, SLIPPAGE_PER_LEG
from cost_calculator import calculate_net_pnl

def log_trade_to_journal(date, strike, entry_price, exit_price, quantity):
    """
    Append a trade result to the CSV journal with Net P&L and Slippage.
    """
    # 1. Apply Slippage (Real-world friction)
    # Entry Sell: We get 0.5 pts LESS
    # Exit Buy: We pay 0.5 pts MORE
    adj_entry = entry_price - SLIPPAGE_PER_LEG
    adj_exit = exit_price + SLIPPAGE_PER_LEG
    
    # 2. Calculate Net P&L
    net_pnl, total_costs = calculate_net_pnl(adj_entry, adj_exit, quantity)
    gross_pnl = (entry_price - exit_price) * quantity
    
    trade_data = {
        'date': date,
        'strike': strike,
        'gross_pnl': round(gross_pnl, 2),
        'net_pnl': round(net_pnl, 2),
        'costs': round(total_costs, 2),
        'slippage_impact': round(SLIPPAGE_PER_LEG * 2 * quantity, 2),
        'points_captured': round(entry_price - exit_price, 2)
    }
    
    df = pd.DataFrame([trade_data])
    
    # Write to file
    header = not os.path.exists(TRADES_CSV_PATH)
    df.to_csv(TRADES_CSV_PATH, mode='a', index=False, header=header)
    
    return trade_data

def get_weekly_stats():
    """
    Aggregate the last 5 trading days for a weekly report.
    """
    if not os.path.exists(TRADES_CSV_PATH):
        return None
        
    df = pd.read_csv(TRADES_CSV_PATH)
    if len(df) == 0: return None
    
    # Last 5 records
    recent = df.tail(5)
    
    stats = {
        'total_net_pnl': recent['net_pnl'].sum(),
        'win_rate': (recent['net_pnl'] > 0).mean() * 100,
        'total_trades': len(recent),
        'best_day': recent['net_pnl'].max(),
        'worst_day': recent['net_pnl'].min()
    }
    return stats
