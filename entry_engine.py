# entry_engine.py
from regime_detector import detect_regime, Regime
from strike_selector import get_straddle_strikes, get_strangle_strikes, get_iron_condor_strikes
from config import NIFTY_LOT_SIZE
from logger import log_trade

def get_entry_trades(spot, vix, adx, dte, lots=1):
    """
    Determine the trades to execute at 9:20 AM.
    """
    regime = detect_regime(vix, adx)
    quantity = lots * NIFTY_LOT_SIZE
    trades = []
    
    if regime == Regime.CALM:
        # MODE 1: ATM Short Straddle
        ce_strike, pe_strike = get_straddle_strikes(spot)
        trades.append({"symbol": "NIFTY", "strike": ce_strike, "type": "CE", "action": "SELL", "qty": quantity})
        trades.append({"symbol": "NIFTY", "strike": pe_strike, "type": "PE", "action": "SELL", "qty": quantity})
        # Note: In a real system, we'd also add the 500-pt OTM hedges here for margin/safety
        
    elif regime == Regime.NORMAL:
        # MODE 2: VIX-Adjusted Short Strangle
        ce_strike, pe_strike = get_strangle_strikes(spot, vix, dte)
        trades.append({"symbol": "NIFTY", "strike": ce_strike, "type": "CE", "action": "SELL", "qty": quantity})
        trades.append({"symbol": "NIFTY", "strike": pe_strike, "type": "PE", "action": "SELL", "qty": quantity})
        
    elif regime == Regime.VOLATILE:
        # MODE 3: Iron Condor
        sce, lce, spe, lpe = get_iron_condor_strikes(spot, vix, dte)
        # Short Leg
        trades.append({"symbol": "NIFTY", "strike": sce, "type": "CE", "action": "SELL", "qty": quantity})
        # Hedge Leg
        trades.append({"symbol": "NIFTY", "strike": lce, "type": "CE", "action": "BUY", "qty": quantity})
        # Short Leg
        trades.append({"symbol": "NIFTY", "strike": spe, "type": "PE", "action": "SELL", "qty": quantity})
        # Hedge Leg
        trades.append({"symbol": "NIFTY", "strike": lpe, "type": "PE", "action": "BUY", "qty": quantity})
        
    # Log the strategy decision
    for trade in trades:
        log_trade(trade['action'], trade['symbol'], trade['strike'], trade['qty'], 0.0, f"Initial 9:20 Entry ({regime})")
        
    return trades

if __name__ == "__main__":
    # Test cases
    spot = 23432
    vix = 13.5
    adx = 18
    dte = 2
    
    print(f"9:20 Entry Strategy (VIX {vix}, ADX {adx}):")
    trades = get_entry_trades(spot, vix, adx, dte)
    for t in trades:
        print(f" {t['action']} {t['strike']} {t['type']} x {t['qty']}")
