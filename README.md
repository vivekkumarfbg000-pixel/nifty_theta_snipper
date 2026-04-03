# Nifty Theta Sniper v2 🚀

A high-performance, regime-adaptive Nifty option selling strategy designed for consistent 5–10% monthly returns. This system is integrated with the Upstox API for both historical research and live execution.

## 🛠️ Project Structure

- `main.py`: The high-level orchestrator for the strategy logic.
- `live_trader.py`: The final execution loop for **Live/Paper Trading**.
- `backtest_full.py`: 30-day historical backtester utilizing real Upstox data.
- `optimizer.py`: Automated Stop-Loss/Take-Profit parameter tuning.
- `upstox_client.py`: Data fetcher for Spot, VIX, and Options.
- `config.py`: Centralized configuration for risk, timing, and capital.

## ✨ Core Strategy: Regime-Adaptive Logic

The system automatically switches strategies at **9:20 AM** based on India VIX:
- **India VIX < 14**: Executes an **ATM Short Straddle** (30% SL).
- **India VIX 14–20**: Executes a **VIX-Adjusted Strangle** (40% SL).
- **India VIX > 20**: Executes a **Hedged Iron Condor** (60% SL on max risk).

## 🚀 Getting Started

### 1. Requirements
Ensure you have Python installed and the following libraries:
```bash
py -m pip install requests pandas numpy upstox-python
```

### 2. Configuration
Open `config.py` and verify your **Upstox Access Token** and **Capital** (Default is ₹5,00,000).

### 3. Run a Backtest
Validate the strategy against actual historical data from March 2026:
```bash
py backtest_full.py
```

### 4. Start Live Paper Trading
Run the system in simulation mode to verify real-time execution logic:
```bash
py live_trader.py
```

## 🛡️ Risk Management
- **3% Daily Loss Cap**: Automatically stops trading for the day if breached.
- **5% Monthly Drawdown Circuit Breaker**: Disables the strategy for the month to protect capital.
- **Statutory Costs**: All calculations account for the **April 2026 STT increases (0.15%)** and SEBI charges.

---
> [!CAUTION]
> By default, `live_trader.py` is in `PAPER_TRADING_MODE = True`. To use real capital, you must manually set this to `False` in the script.
