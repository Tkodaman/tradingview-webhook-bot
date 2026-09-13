import alpaca_trade_api as tradeapi

api = tradeapi.REST('PKIKFGYOOUV5TTHG4SF35BV2AC', 'G3G2kWbmo3d6EwLs3McVuY5i2oPMe6Htt9eQHNcoa6Rk', 'https://paper-api.alpaca.markets')

try:
    orders = api.list_orders(status="open")
    for o in orders:
        print(f"Order: {o.id}, Symbol: {o.symbol}, Side: {o.side}, Type: {o.type}, Class: {o.order_class}, Stop: {o.stop_price}, Limit: {o.limit_price}")
except Exception as e:
    print("Error:", e)
