import alpaca_trade_api as tradeapi
import os

from dotenv import load_dotenv
load_dotenv()
api = tradeapi.REST(
    os.environ["ALPACA_API_KEY"],
    os.environ["ALPACA_SECRET_KEY"],
    "https://paper-api.alpaca.markets"
)

try:
    print("Canceling orders...")
    # api.cancel_all_orders()  # No, that cancels everything. We only want to cancel LINK orders.
    orders = api.list_orders(status="open")
    for o in orders:
        if o.symbol == 'LINK/USD':
            api.cancel_order(o.id)
    print("Closing LINKUSD...")
    print(api.close_position('LINKUSD'))
except Exception as e:
    print("Failed LINKUSD:", e)
