import alpaca_trade_api as tradeapi
import os

api = tradeapi.REST('PKIKFGYOOUV5TTHG4SF35BV2AC', 'G3G2kWbmo3d6EwLs3McVuY5i2oPMe6Htt9eQHNcoa6Rk', 'https://paper-api.alpaca.markets')

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
