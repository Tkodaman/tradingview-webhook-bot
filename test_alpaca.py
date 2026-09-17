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
    print(api.get_asset('LINK/USD'))
    print("LINK/USD SUCCESS")
except Exception as e:
    print("LINK/USD FAIL:", e)

try:
    print(api.get_asset('LINKUSD'))
    print("LINKUSD SUCCESS")
except Exception as e:
    print("LINKUSD FAIL:", e)
