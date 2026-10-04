import asyncio, json, time
from schemas.webhook import WebhookSignal
from services.order_router import process_order
from services.market_feed.live_stream import live_trade_manager
from core.config import settings

signal = WebhookSignal(
    passphrase=settings.passphrase,
    action='BUY',
    symbol='BTCUSDT',
    price=65000.0,
    quantity=0.001,
    take_profit=66000.0,
    stop_loss=64000.0,
    account_equity=100.0,
    market_position='long',
    timestamp_ms=int(time.time() * 1000)
)

async def run():
    print('Starting mock execution...')
    res = process_order(signal)
    print('Result:', res)
    for sym, p in live_trade_manager.positions.items():
        print(f'{sym}: {p.status} - ID: {p.broker_order_id}')

asyncio.run(run())
