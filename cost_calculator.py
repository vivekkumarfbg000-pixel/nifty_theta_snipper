# cost_calculator.py
from config import STT_SELL_SIDE_PCT, BROKERAGE_PER_ORDER, EXCHANGE_TRANSACTION_MODIFIER, GST_PCT, NIFTY_LOT_SIZE

def calculate_costs(premium, quantity, lot_size=NIFTY_LOT_SIZE):
    """
    Calculate statutory and operational costs for a sell transaction.
    
    Formula:
    STT = 0.15% on Sell side premium
    Brokerage = Flat order fee
    Exchange = turnover * modifier
    GST = 18% on (Brokerage + Exchange)
    """
    turnover = premium * quantity
    
    stt = turnover * STT_SELL_SIDE_PCT
    brokerage = BROKERAGE_PER_ORDER
    exchange_charges = turnover * EXCHANGE_TRANSACTION_MODIFIER
    
    gst = (brokerage + exchange_charges) * GST_PCT
    
    # Small regulatory fees (SEBI, Stamp Duty)
    sebi_stamp_fees = turnover * 0.000002  # Approximately 0.0002%
    
    total_costs = stt + brokerage + exchange_charges + gst + sebi_stamp_fees
    
    return total_costs

def calculate_net_pnl(entry_premium, exit_premium, quantity):
    """
    Calculate the net P&L after all costs for a trade.
    """
    gross_pnl = (entry_premium - exit_premium) * quantity
    
    # Costs are incurred twice (Entry Sell and Exit Buy)
    # Note: STT is only on the SELL side.
    entry_costs = calculate_costs(entry_premium, quantity)
    
    # For the Exit Buy side:
    # STT is NOT charged on Buy Side for Options.
    # Brokerage, Exchange, GST apply.
    buy_turnover = exit_premium * quantity
    buy_brokerage = BROKERAGE_PER_ORDER
    buy_exchange = buy_turnover * EXCHANGE_TRANSACTION_MODIFIER
    buy_gst = (buy_brokerage + buy_exchange) * GST_PCT
    buy_costs = buy_brokerage + buy_exchange + buy_gst
    
    net_pnl = gross_pnl - (entry_costs + buy_costs)
    
    return net_pnl, entry_costs + buy_costs

if __name__ == "__main__":
    # Test cases
    entry_pr = 200
    exit_pr = 50
    qty = 50  # 1 lot
    
    net, costs = calculate_net_pnl(entry_pr, exit_pr, qty)
    print(f"Gross P&L: {(entry_pr - exit_pr) * qty}")
    print(f"Total Costs: {costs:.2f}")
    print(f"Net P&L: {net:.2f}")
    print(f"Profit Efficiency: {(net / ((entry_pr - exit_pr) * qty)) * 100:.2f}%")
