import alpaca_trade_api as tradeapi

api = tradeapi.REST('PKIKFGYOOUV5TTHG4SF35BV2AC', 'G3G2kWbmo3d6EwLs3McVuY5i2oPMe6Htt9eQHNcoa6Rk', 'https://paper-api.alpaca.markets')

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
