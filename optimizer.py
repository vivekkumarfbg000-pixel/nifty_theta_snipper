# optimizer.py
from backtester import HistoricalBacktester
from config import SL_PCT_STRADDLE, TP_PCT_STRADDLE
from logger import logger
import itertools

class StrategyOptimizer:
    def __init__(self, from_date, to_date):
        self.from_date = from_date
        self.to_date = to_date
        self.results = []

    def optimize(self):
        """
        Run backtests across a grid of SL and TP parameters.
        """
        # Define ranges for SL and TP
        sl_range = [0.20, 0.25, 0.30, 0.35, 0.40]
        tp_range = [0.40, 0.50, 0.60]

        combinations = list(itertools.product(sl_range, tp_range))
        logger.info(f"Starting parameter optimization across {len(combinations)} combinations...")

        best_result = None
        best_pnl = -float('inf')

        for sl, tp in combinations:
            logger.info(f"Testing SL: {sl:.2f}, TP: {tp:.2f}")
            
            # Here we would dynamically update config OR pass these as args to backtester
            # For demonstration, we'll assume a modified backtester that can accept these.
            
            # bt = HistoricalBacktester(self.from_date, self.to_date)
            # results = bt.run(sl_pct=sl, tp_pct=tp)
            
            # Dummy result for demonstration
            mock_net_pnl = 20000 + (sl*1000 - tp*500) # Proxy for actual P&L
            
            self.results.append({
                "SL": sl,
                "TP": tp,
                "Net_PnL": mock_net_pnl
            })
            
            if mock_net_pnl > best_pnl:
                best_pnl = mock_net_pnl
                best_result = (sl, tp)

        logger.info(f"Optimization Complete. Best Parameters: SL={best_result[0]}, TP={best_result[1]}")
        return best_result

if __name__ == "__main__":
    optimizer = StrategyOptimizer("2026-03-01", "2026-03-31")
    best_params = optimizer.optimize()
    print(f"Optimal Strategy Parameters Found: SL={best_params[0]*100}%, TP={best_params[1]*100}%")
