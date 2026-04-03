# upstox_orders.py
import upstox_client
from upstox_client.rest import ApiException
from config import UPSTOX_ACCESS_TOKEN
from logger import logger

class UpstoxOrderEngine:
    def __init__(self, token=UPSTOX_ACCESS_TOKEN, paper_trading=True):
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = token
        self.api_client = upstox_client.ApiClient(self.configuration)
        self.order_api = upstox_client.OrderApi(self.api_client)
        self.paper_trading = paper_trading

    def place_option_order(self, inst_key, side, qty, product='I', order_type='MARKET', price=0.0):
        """
        Place a Nifty option order.
        side: 'BUY' or 'SELL'
        """
        if self.paper_trading:
            logger.info(f"[PAPER] Order Placed: {side} {qty} lots of {inst_key} @ {order_type}")
            return {"status": "success", "order_id": "PAPER_12345"}

        order_body = upstox_client.PlaceOrderRequest(
            quantity=qty,
            product=product,
            validity='DAY',
            price=price,
            instrument_token=inst_key,
            order_type=order_type,
            transaction_type=side,
            disclosed_quantity=0,
            trigger_price=0.0,
            is_amo=False
        )

        try:
            api_response = self.order_api.place_order(order_body, api_version='2.0')
            logger.info(f"[LIVE] Order Successful: {api_response.data.order_id}")
            return {"status": "success", "order_id": api_response.data.order_id}
        except ApiException as e:
            logger.error(f"[LIVE] API Exception: {str(e)}")
            return {"status": "error", "message": str(e)}

    def square_off_all(self, positions):
        """
        Square off all active positions.
        """
        logger.warning(f"SQUARING OFF ALL {len(positions)} POSITIONS")
        for pos_key, data in positions.items():
            # Example key mapping to instrument
            inst_key = data['inst_key']
            qty = data['qty']
            side = 'BUY' if data['type'] == 'SELL' else 'SELL'
            self.place_option_order(inst_key, side, qty)

if __name__ == "__main__":
    # Test Paper Order
    engine = UpstoxOrderEngine(paper_trading=True)
    res = engine.place_option_order("NSE_FO|12345", "SELL", 50)
    print(res)
