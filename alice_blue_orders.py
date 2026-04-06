# alice_blue_orders.py
from pya3 import Aliceblue, TransactionType, OrderType, ProductType
from alice_blue_helper import AliceBlueClient
from logger import logger

class AliceBlueOrderEngine:
    def __init__(self, paper_trading=True):
        self.client = AliceBlueClient()
        self.alice = self.client.alice
        self.paper_trading = paper_trading

    def place_option_order(self, instrument, side, qty, product='I', order_type='MARKET', price=0.0):
        """
        Place a Nifty option order on Alice Blue.
        side: 'BUY' or 'SELL'
        """
        if self.paper_trading:
            logger.info(f"[PAPER-ALICE] Order Placed: {side} {qty} of {instrument['TSymbol']} @ {order_type}")
            return {"status": "success", "order_id": "PAPER_ALICE_12345"}

        if not self.alice:
            logger.error("Alice Blue Client not initialized.")
            return {"status": "error", "message": "Client not initialized"}

        t_type = TransactionType.Buy if side == 'BUY' else TransactionType.Sell
        o_type = OrderType.Market if order_type == 'MARKET' else OrderType.Limit
        p_type = ProductType.Intraday if product == 'I' else ProductType.Delivery

        try:
            res = self.alice.place_order(
                transaction_type=t_type,
                instrument=instrument,
                quantity=qty,
                order_type=o_type,
                product_type=p_type,
                price=price,
                trigger_price=0.0,
                stop_loss=None,
                trailing_sl=None,
                is_amo=False
            )
            if res and res.get('status') == 'success':
                logger.info(f"[LIVE-ALICE] Order Successful: {res.get('data', {}).get('oms_order_id')}")
                return {"status": "success", "order_id": res.get('data', {}).get('oms_order_id')}
            else:
                logger.error(f"[LIVE-ALICE] Order Failed: {res}")
                return {"status": "error", "message": str(res)}
        except Exception as e:
            logger.error(f"[LIVE-ALICE] Exception: {str(e)}")
            return {"status": "error", "message": str(e)}

    def square_off_all(self, positions):
        """
        Square off all active positions.
        """
        logger.warning(f"ALICE: SQUARING OFF ALL {len(positions)} POSITIONS")
        for pos_key, data in positions.items():
            # In Alice Blue, data['instrument'] should be the instrument object
            instrument = data['instrument']
            qty = data['qty']
            side = 'BUY' if data['type'] == 'SELL' else 'SELL'
            self.place_option_order(instrument, side, qty)

if __name__ == "__main__":
    # Test Paper Order
    engine = AliceBlueOrderEngine(paper_trading=True)
    # mock instrument
    mock_inst = {'TSymbol': 'NIFTY24APR19000CE', 'Token': '12345'}
    res = engine.place_option_order(mock_inst, "SELL", 50)
    print(res)
