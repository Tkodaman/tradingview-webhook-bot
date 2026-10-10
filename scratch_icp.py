import sys
import asyncio
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.broker.binance_bridge import BinanceBroker
from services.broker.market_data_fetcher import MarketDataFetcher

def get_icp():
    b = BinanceBroker()
    prices = b.get_realtime_prices(["ICPUSDT"])
    
    try:
        fetcher = MarketDataFetcher()
        adv = asyncio.run(fetcher.fetch_realtime_data("ICPUSDT"))
        print(f"PRICE: {prices}")
        print(f"ADVANCED: {adv}")
    except Exception as e:
        print(f"PRICE: {prices}, ERR: {e}")

if __name__ == "__main__":
    get_icp()
