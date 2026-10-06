import asyncio
import os
import sys
sys.path.append(os.path.abspath('.'))
from core.config import settings
from services.order_router import process_order
from schemas.webhook import WebhookSignal
import time

def test_order():
    print("Testing Binance Paper Trade...")
    signal = WebhookSignal(
        passphrase=settings.passphrase,
        action="BUY",
        symbol="DOGEUSDT",
        price=0.10,
        quantity=100.0,
        take_profit=0.12,
        stop_loss=0.09,
        account_equity=100.0,
        market_position="long",
        timestamp_ms=int(time.time() * 1000),
        indicators={"volume_ratio": 5.0, "rsi": 45.0, "adx": 30.0},
        macro_tags=["TEST_ORDER"]
    )
    # process_order is NOT async, it returns a dict
    res = process_order(signal)
    print(f"Result: {res}")

if __name__ == "__main__":
    test_order()
