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
    orders = api.list_orders(status="open")
    for o in orders:
        print(f"Order: {o.id}, Symbol: {o.symbol}, Side: {o.side}, Type: {o.type}, Class: {o.order_class}, Stop: {o.stop_price}, Limit: {o.limit_price}")
except Exception as e:
    print("Error:", e)
