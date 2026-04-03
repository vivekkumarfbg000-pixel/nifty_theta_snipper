# reentry_engine.py
from datetime import datetime, timedelta
from config import MAX_REENTRIES_PER_DAY, REENTRY_COOLDOWN_MINUTES, MAX_REENTRY_TIME, REENTRY_POSITION_SIZE_MODIFIER
from logger import log_trade

class ReentryManager:
    def __init__(self):
        self.reentry_counts = 0
        self.last_sl_time = None
        self.last_sl_leg = None

    def register_sl_hit(self, leg_key, current_time_str):
        """
        Record an SL hit event.
        """
        self.last_sl_time = datetime.strptime(current_time_str, "%H:%M:%S")
        self.last_sl_leg = leg_key

    def is_eligible_for_reentry(self, current_time_str, current_vix, entry_vix, current_adx):
        """
        Check re-entry eligibility based on the decision matrix.
        """
        if self.reentry_counts >= MAX_REENTRIES_PER_DAY:
            return False, "Max Re-entries Exceeded"
            
        if self.last_sl_time is None:
            return False, "No SL Hit to Trigger Re-entry"
            
        current_time = datetime.strptime(current_time_str, "%H:%M:%S")
        max_reentry_time = datetime.strptime(MAX_REENTRY_TIME, "%H:%M:%S").time()
        
        # 1. Rule: Max Re-entry Time (1:30 PM)
        if current_time.time() > max_reentry_time:
            return False, "Too Late for Re-entry"
            
        # 2. Rule: Cooldown Period (15 min)
        if current_time < (self.last_sl_time + timedelta(minutes=REENTRY_COOLDOWN_MINUTES)):
            return False, f"Inside Cooldown ({REENTRY_COOLDOWN_MINUTES} min)"
            
        # 3. Rule: VIX Spike Monitor
        vix_change_pct = (current_vix - entry_vix) / entry_vix if entry_vix != 0 else 0
        if vix_change_pct > 0.05:
            return False, "VIX Spiked > 5% since Entry"
            
        # 4. Rule: ADX Trend Check
        if current_adx > 25:
            return False, "Market Trending (ADX > 25)"
            
        return True, "Eligible"

    def execute_reentry(self, leg_type, current_spot, original_qty):
        """
        Returns new re-entry trade details.
        """
        self.reentry_counts += 1
        new_qty = int(original_qty * REENTRY_POSITION_SIZE_MODIFIER)
        
        # Logic: If CE hit SL, sell new CE at ATM + 100 (OTM shift)
        # If PE hit SL, sell new PE at ATM - 100 (OTM shift)
        from strike_selector import round_strike
        
        atm = round_strike(current_spot)
        new_strike = atm + 100 if leg_type == "CE" else atm - 100
        
        reentry_trade = {
            "symbol": "NIFTY",
            "strike": new_strike,
            "type": leg_type,
            "action": "SELL",
            "qty": new_qty,
            "reason": f"Re-entry #{self.reentry_counts} after {leg_type} SL hit"
        }
        
        log_trade("REENTRY", reentry_trade['symbol'], reentry_trade['strike'], reentry_trade['qty'], 0.0, reentry_trade['reason'])
        return reentry_trade

if __name__ == "__main__":
    # Test cases
    manager = ReentryManager()
    
    # Simulating CE SL Hit at 10:00 AM
    manager.register_sl_hit("CE", "10:00:00")
    
    # Check at 10:05 AM (Should fail due to cooldown)
    eligible, reason = manager.is_eligible_for_reentry("10:05:00", 16.5, 16.0, 20)
    print(f"Check at 10:05: {eligible} | {reason}")
    
    # Check at 10:20 AM (Should pass)
    eligible, reason = manager.is_eligible_for_reentry("10:20:00", 16.5, 16.0, 20)
    print(f"Check at 10:20: {eligible} | {reason}")
    
    # Execute re-entry
    if eligible:
        t = manager.execute_reentry("CE", 23530, 50)
        print(f"Re-entry Trade: {t}")
