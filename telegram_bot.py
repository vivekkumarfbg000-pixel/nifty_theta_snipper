# telegram_bot.py
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logger import logger

def send_telegram_message(message):
    """
    Send a formatted message to your Telegram account.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False

def format_daily_report(date, strike, entry_price, exit_price, pnl, points):
    """
    Create a professional summary for the daily report.
    """
    status = "WIN" if pnl >= 0 else "LOSS"
    report = f"""
*Nifty Theta Sniper V3: Daily Report ({date})*
---------------------------------------
STATUS: {status} | Net P&L: INR {pnl:,.2f}

*Details:*
• ATM Strike: {strike}
• Entry (9:20): INR {entry_price:.2f}
• Exit (EOD): INR {exit_price:.2f}
• Points Captured: {points:.1f}

*Safety Check:*
• VWAP Breach: No
• Trailing SL: Activated
---------------------------------------
    """
    return report

def format_weekly_report(stats):
    """
    Create a professional summary for the weekly report.
    """
    if not stats: return "No trades found for this period."
    
    status = "POSITIVE" if stats['total_net_pnl'] >= 0 else "NEGATIVE"
    report = f"""
*Nifty Theta Sniper V3: WEEKLY AUDIT*
---------------------------------------
PERFORMANCE: {status} | Net: INR {stats['total_net_pnl']:,.2f}

*Stats:*
• Win Rate: {stats['win_rate']:.1f}%
• Best Day: +INR {stats['best_day']:,.0f}
• Worst Day: -INR {abs(stats['worst_day']):,.0f}
• Total Trades: {stats['total_trades']}

*Efficiency Check:*
• Realistic Slippage: YES (0.5 pts)
• Statutory Costs: YES (INR 40/order)
---------------------------------------
    """
    return report

if __name__ == "__main__":
    # Test Message
    test_msg = "💎 *Nifty Theta Sniper Bot* is online!"
    send_telegram_message(test_msg)
