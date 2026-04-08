import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import TRADES_CSV_PATH

app = FastAPI(title="Nifty Theta Sniper Dashboard API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_trades_df():
    if not os.path.exists(TRADES_CSV_PATH):
        return pd.DataFrame()
    return pd.read_csv(TRADES_CSV_PATH)

@app.get("/api/trades")
async def get_trades():
    df = get_trades_df()
    if df.empty:
        return []
    # Convert to list of dicts, sorted by date descending
    return df.sort_values('date', ascending=False).to_dict(orient='records')

@app.get("/api/stats")
async def get_stats():
    df = get_trades_df()
    if df.empty:
        return {
            "total_net_pnl": 0,
            "win_rate": 0,
            "total_trades": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "equity_curve": []
        }
    
    # Calculate Metrics
    total_net_pnl = df['net_pnl'].sum()
    win_rate = (df['net_pnl'] > 0).mean() * 100
    
    # Equity Curve
    equity = df.sort_values('date')['net_pnl'].cumsum().tolist()
    dates = df.sort_values('date')['date'].tolist()
    
    return {
        "total_net_pnl": round(total_net_pnl, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(df),
        "best_trade": round(df['net_pnl'].max(), 2),
        "worst_trade": round(df['net_pnl'].min(), 2),
        "avg_trade": round(df['net_pnl'].mean(), 2),
        "equity_curve": [{"date": d, "value": v} for d, v in zip(dates, equity)]
    }

# Serve the frontend files
if os.path.exists("dashboard"):
    app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
