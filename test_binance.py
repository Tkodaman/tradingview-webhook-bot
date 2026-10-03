from services.broker.binance_bridge import BinanceBroker

b = BinanceBroker(paper=False)
print('USDT Balance:', b.get_account_balance())

