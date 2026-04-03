# risk_manager.py
from config import TOTAL_CAPITAL, MAX_DAILY_LOSS_PCT, MAX_MONTHLY_LOSS_PCT
from logger import logger

class RiskManager:
    def __init__(self, initial_capital=TOTAL_CAPITAL):
        self.initial_capital = initial_capital
        self.daily_pnl = 0.0
        self.monthly_pnl = 0.0
        self.is_circuit_broken = False
        self.is_trailing_active = False

    def check_trailing_activation(self, current_pnl):
        """
        Check if profit has reached the trigger for VWAP-Trailing SL.
        """
        from config import TRAILING_SL_TRIGGER_AMT
        if not self.is_trailing_active and current_pnl >= TRAILING_SL_TRIGGER_AMT:
            self.is_trailing_active = True
            logger.info(f"[RISK] VWAP Trailing SL Activated (Profit: {current_pnl} >= {TRAILING_SL_TRIGGER_AMT})")
            return True
        return False

    def update_pnl(self, net_pnl):
        """
        Increment the daily and monthly P&L.
        """
        self.daily_pnl += net_pnl
        self.monthly_pnl += net_pnl
        self.check_circuit_breakers()

    def check_circuit_breakers(self):
        """
        Check if daily or monthly loss limits have been breached.
        """
        daily_loss_limit = -self.initial_capital * MAX_DAILY_LOSS_PCT
        monthly_loss_limit = -self.initial_capital * MAX_MONTHLY_LOSS_PCT
        
        if self.daily_pnl <= daily_loss_limit:
            logger.warning(f"[RISK] Daily Loss Limit Breached: {self.daily_pnl} (Limit: {daily_loss_limit})")
            self.is_circuit_broken = True
            
        if self.monthly_pnl <= monthly_loss_limit:
            logger.warning(f"[RISK] Monthly Loss Limit Breached: {self.monthly_pnl} (Limit: {monthly_loss_limit})")
            self.is_circuit_broken = True

    def reset_daily(self):
        """
        Reset daily P&L (usually called at EOD).
        """
        self.daily_pnl = 0.0
        self.is_circuit_broken = False

    def can_trade(self):
        """
        Return True if circuit breakers are NOT triggered.
        """
        return not self.is_circuit_broken

if __name__ == "__main__":
    # Test cases
    rm = RiskManager(500000)
    print(f"Can trade initially: {rm.can_trade()}")
    
    # Simulating a loss of ₹10k
    rm.update_pnl(-10000)
    print(f"Daily P&L: {rm.daily_pnl} | Can trade: {rm.can_trade()}")
    
    # Simulating reaching the -₹15k daily limit
    rm.update_pnl(-6000)
    print(f"Daily P&L: {rm.daily_pnl} | Can trade: {rm.can_trade()}")
