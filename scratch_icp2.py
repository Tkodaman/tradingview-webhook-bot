import json
from services.broker.binance_bridge import BinanceBroker

b = BinanceBroker()
prices = b.get_realtime_prices(["ICPUSDT", "BCHUSDT", "MINAUSDT"])
print(json.dumps(prices))
