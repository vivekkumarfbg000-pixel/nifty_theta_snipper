# regime_detector.py
from config import VIX_THRESHOLD_CALM, VIX_THRESHOLD_NORMAL, ADX_THRESHOLD_TREND
from logger import log_regime

class Regime:
    CALM = "CALM"          # Straddle mode
    NORMAL = "NORMAL"      # Strangle mode
    VOLATILE = "VOLATILE"  # Iron Condor mode

def detect_regime(vix, adx):
    """
    Classify market regime based on VIX and ADX.
    
    Logic:
    - CALM: VIX < 14 AND ADX < 20 (Mean Reversion, high decay)
    - NORMAL: VIX 14-20 AND ADX < 25 (Standard range-bound)
    - VOLATILE: VIX > 20 OR ADX > 25 (Strong trend or high fear)
    """
    if vix < VIX_THRESHOLD_CALM and adx < 20:
        regime = Regime.CALM
    elif vix <= VIX_THRESHOLD_NORMAL and adx < ADX_THRESHOLD_TREND:
        regime = Regime.NORMAL
    else:
        regime = Regime.VOLATILE
    
    log_regime(vix, adx, regime)
    return regime

if __name__ == "__main__":
    # Test cases
    print(f"VIX 12, ADX 15 -> {detect_regime(12, 15)}")
    print(f"VIX 18, ADX 22 -> {detect_regime(18, 22)}")
    print(f"VIX 25, ADX 10 -> {detect_regime(25, 10)}")
    print(f"VIX 15, ADX 30 -> {detect_regime(15, 30)}")
