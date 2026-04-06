# webhook_orders.py
import json
import requests
from config import WEBHOOK_URL, WEBHOOK_PAYLOAD_FORMAT
from logger import logger

class WebhookOrderEngine:
    def __init__(self, paper_trading=True):
        self.webhook_url = WEBHOOK_URL
        self.paper_trading = paper_trading
        
    def place_option_order(self, symbol, side, qty):
        """
        Sends a POST request to the 1lyalgos webhook.
        """
        if self.paper_trading:
            logger.info(f"[WEBHOOK-PAPER] Signal Sent for {symbol}: {side} {qty}")
            return True
            
        try:
            # Prepare Payload by filling the template
            payload = json.dumps(WEBHOOK_PAYLOAD_FORMAT).replace("{symbol}", symbol).replace("{side}", side).replace("{qty}", str(qty))
            payload_dict = json.loads(payload)
            
            logger.info(f"Sending Webhook Signal to {self.webhook_url}...")
            response = requests.post(self.webhook_url, json=payload_dict, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Webhook response: {response.text}")
            return True
            
        except Exception as e:
            logger.error(f"Webhook Signal Failed for {symbol}: {str(e)}")
            return False

    def square_off_all(self, positions):
        """
        Squares off all active positions by sending opposite signals.
        """
        logger.info(f"Webhook Square-off Signal for {len(positions)} positions.")
        for pos_key, pos_data in positions.items():
            opp_side = "BUY" if pos_data['type'] == "SELL" else "SELL"
            self.place_option_order(pos_data['instrument'], opp_side, pos_data['qty'])
