# exit_engine.py
from regime_detector import Regime
from config import SL_PCT_STRADDLE, SL_PCT_STRANGLE, TP_PCT_STRADDLE, TP_PCT_STRANGLE, EXIT_TIME_LIMIT
from datetime import datetime

class ExitAction:
    HOLD = "HOLD"
    EXIT_LEG = "EXIT_LEG"
    EXIT_ALL = "EXIT_ALL"

def check_exit_rules(positions, current_prices, current_time_str, regime, vwap_breached=False):
    """
    Check all exit rules and return required actions.
    
    positions: dict where key is (symbol, strike, type) and value is entry_premium
    current_prices: dict where key is (symbol, strike, type) and value is current_premium
    vwap_breached: bool indicating if the VWAP exit condition (e.g. 2 candle close) is met
    """
    actions = {}
    
    # Pre-parse time
    current_time = datetime.strptime(current_time_str, "%H:%M:%S").time()
    exit_time = datetime.strptime(EXIT_TIME_LIMIT, "%H:%M:%S").time()
    
    # 1. Rule: Time-based Exit (3:15 PM)
    if current_time >= exit_time:
        for pos_key in positions:
            actions[pos_key] = {"action": ExitAction.EXIT_ALL, "reason": "Time Limit Reached"}
        return actions

    # 1.5 Rule: VWAP Exit (New)
    if vwap_breached:
        for pos_key in positions:
            actions[pos_key] = {"action": ExitAction.EXIT_ALL, "reason": "VWAP Exit (2 Candle Close Above)"}
        return actions

    # 2. Rule: Combine Premium Target (TP)
    total_entry_premium = sum(val for val in positions.values() if isinstance(val, (int, float)))
    total_current_premium = sum(val for val in current_prices.values() if isinstance(val, (int, float)))
    
    if total_current_premium == 0 and total_entry_premium > 0:
        return actions # Do not evaluate TPs/SLs if price feed is completely dead/missing

    tp_pct = TP_PCT_STRADDLE if regime == Regime.CALM else TP_PCT_STRANGLE
    if total_current_premium <= (total_entry_premium * (1 - tp_pct)):
        for pos_key in positions:
            actions[pos_key] = {"action": ExitAction.EXIT_ALL, "reason": "Combined TP Reached"}
        return actions

    # 3. Rule: Individual Leg SL
    sl_pct = SL_PCT_STRADDLE if regime == Regime.CALM else SL_PCT_STRANGLE
    
    for pos_key, entry_pr in positions.items():
        curr_pr = current_prices.get(pos_key)
        if curr_pr is None:
            continue
            
        if curr_pr >= (entry_pr * (1 + sl_pct)):
            actions[pos_key] = {"action": ExitAction.EXIT_LEG, "reason": "Individual Leg SL Hit"}
            
    # Note: Trailing SL can be added here or in a wrapper layer.
    
    return actions

if __name__ == "__main__":
    # Test cases
    regime = Regime.CALM
    positions = {("NIFTY", 23450, "CE"): 180, ("NIFTY", 23450, "PE"): 170}
    
    # Scenario: SL Hit on CE
    curr_prices = {("NIFTY", 23450, "CE"): 240, ("NIFTY", 23450, "PE"): 150}
    actions = check_exit_rules(positions, curr_prices, "10:30:00", regime)
    print(f"SL Scenario (10:30): {actions}")
    
    # Scenario: TP Hit
    curr_prices = {("NIFTY", 23450, "CE"): 80, ("NIFTY", 23450, "PE"): 70}
    actions = check_exit_rules(positions, curr_prices, "11:45:00", regime)
    print(f"TP Scenario (11:45): {actions}")
    
    # Scenario: Time Limit Hit
    curr_prices = {("NIFTY", 23450, "CE"): 180, ("NIFTY", 23450, "PE"): 170}
    actions = check_exit_rules(positions, curr_prices, "15:20:00", regime)
    print(f"Time Exit (15:20): {actions}")
