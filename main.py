# main.py
from datetime import datetime
import time
from config import ENTRY_TIME, EXIT_TIME_LIMIT
from logger import logger, log_regime
from regime_detector import detect_regime
from entry_engine import get_entry_trades
from exit_engine import check_exit_rules, ExitAction
from reentry_engine import ReentryManager
from risk_manager import RiskManager
from cost_calculator import calculate_net_pnl

class StrategyOrchestrator:
    def __init__(self):
        self.risk_manager = RiskManager()
        self.reentry_manager = ReentryManager()
        self.active_positions = {}  # key: (symbol, strike, type), value: entry_premium
        self.entry_vix = 0.0
        self.regime = None
        
    def run_day(self, spot_provider, vix_provider, adx_provider, current_time_str):
        """
        Simulate/Execute one step in the trading day.
        """
        curr_time = datetime.strptime(current_time_str, "%H:%M:%S").time()
        entry_t = datetime.strptime(ENTRY_TIME, "%H:%M:%S").time()
        exit_t = datetime.strptime(EXIT_TIME_LIMIT, "%H:%M:%S").time()
        
        # 1. Check if it's entry time
        if curr_time == entry_t and not self.active_positions:
            spot = spot_provider()
            vix = vix_provider()
            adx = adx_provider()
            self.entry_vix = vix
            self.regime = detect_regime(vix, adx)
            
            # Get 9:20 Entry Trades
            trades = get_entry_trades(spot, vix, adx, dte=1) # DTE logic to be refined
            for t in trades:
                if t['action'] == "SELL":
                    pos_key = (t['symbol'], t['strike'], t['type'])
                    self.active_positions[pos_key] = 100.0  # Placeholder entry premium
            logger.info(f"Entered {len(self.active_positions)} positions at 9:20 AM")
            
        # 2. Monitor Active Positions
        if self.active_positions:
            # Check for exits
            current_prices = {k: 95.0 for k in self.active_positions} # Placeholder current prices
            actions = check_exit_rules(self.active_positions, current_prices, current_time_str, self.regime)
            
            for pos_key, action_data in actions.items():
                action = action_data['action']
                reason = action_data['reason']
                
                if action == ExitAction.EXIT_LEG:
                    # Individual SL hit
                    logger.info(f"Exiting Leg {pos_key} due to {reason}")
                    self.reentry_manager.register_sl_hit(pos_key[2], current_time_str)
                    del self.active_positions[pos_key]
                    
                elif action == ExitAction.EXIT_ALL:
                    # TP or Time Exit
                    logger.info(f"Exiting All positions due to {reason}")
                    self.active_positions.clear()
                    break

            # 3. Check for Re-entry
            if not self.active_positions:
                spot = spot_provider()
                vix = vix_provider()
                adx = adx_provider()
                eligible, reason = self.reentry_manager.is_eligible_for_reentry(current_time_str, vix, self.entry_vix, adx)
                
                if eligible:
                    # For simplicity, re-entry on the last leg type that hit SL
                    leg_type = self.reentry_manager.last_sl_leg
                    t = self.reentry_manager.execute_reentry(leg_type, spot, 50) # 50 = original qty
                    pos_key = (t['symbol'], t['strike'], t['type'])
                    self.active_positions[pos_key] = 80.0 # Placeholder re-entry premium
                    logger.info(f"Re-entered {pos_key} after SL hit")

if __name__ == "__main__":
    # Mock data providers
    orchestrator = StrategyOrchestrator()
    
    # Simple simulation loop
    spot_val = 23450
    vix_val = 15.0
    adx_val = 20.0
    
    log_regime(vix_val, adx_val, "NORMAL")
    
    # Run a mock 9:20 Entry
    orchestrator.run_day(lambda: spot_val, lambda: vix_val, lambda: adx_val, "09:20:00")
    
    # Run a mock 10:30 Check (Price stable)
    orchestrator.run_day(lambda: spot_val, lambda: vix_val, lambda: adx_val, "10:30:00")
    
    # Run a mock 15:15 Exit
    orchestrator.run_day(lambda: spot_val, lambda: vix_val, lambda: adx_val, "15:15:00")
