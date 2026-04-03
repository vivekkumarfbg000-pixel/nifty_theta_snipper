# strike_selector.py
import math

def calculate_expected_move(spot, vix, dte):
    """
    Calculate the expected range of the underlying at expiry.
    Formula: Spot * (VIX/100) * sqrt(DTE/365)
    """
    if dte == 0:
        # For 0-DTE, assume at least 0.5% move for safety
        return spot * 0.005
    
    expected_pct_move = (vix / 100.0) * math.sqrt(dte / 365.0)
    return spot * expected_pct_move

def round_strike(price, step=50):
    """
    Round the price to the nearest strike step (default 50 for Nifty).
    """
    return round(price / step) * step

def get_straddle_strikes(spot):
    """
    Get ATM strikes for Short Straddle.
    """
    atm_strike = round_strike(spot)
    return atm_strike, atm_strike

def get_strangle_strikes(spot, vix, dte, multiplier=0.7):
    """
    Get OTM strikes for Short Strangle based on VIX-adjusted Expected Move.
    """
    expected_move = calculate_expected_move(spot, vix, dte)
    
    # CE Strike: Spot + Multiplier * Expected Move
    ce_raw = spot + (multiplier * expected_move)
    ce_strike = round_strike(ce_raw)
    
    # PE Strike: Spot - Multiplier * Expected Move
    pe_raw = spot - (multiplier * expected_move)
    pe_strike = round_strike(pe_raw)
    
    return ce_strike, pe_strike

def get_iron_condor_strikes(spot, vix, dte, spread_width=300):
    """
    Get strikes for Iron Condor (Sell 1.0 Expected Move, Buy 1.0 EM + Width).
    """
    expected_move = calculate_expected_move(spot, vix, dte)
    
    # Short Strikes
    short_ce = round_strike(spot + expected_move)
    short_pe = round_strike(spot - expected_move)
    
    # Long Strikes (Hedges)
    long_ce = short_ce + spread_width
    long_pe = short_pe - spread_width
    
    return short_ce, long_ce, short_pe, long_pe

if __name__ == "__main__":
    # Test cases
    nifty_spot = 23432
    vix = 16
    dte = 2
    
    em = calculate_expected_move(nifty_spot, vix, dte)
    print(f"Expected Move (2 DTE, VIX 16): {em:.2f} pts")
    
    ce, pe = get_straddle_strikes(nifty_spot)
    print(f"Straddle Strikes: CE {ce}, PE {pe}")
    
    ce, pe = get_strangle_strikes(nifty_spot, vix, dte)
    print(f"Strangle Strikes: CE {ce}, PE {pe}")
    
    sce, lce, spe, lpe = get_iron_condor_strikes(nifty_spot, vix, dte)
    print(f"Iron Condor: Short CE {sce}, Long CE {lce} | Short PE {spe}, Long PE {lpe}")
