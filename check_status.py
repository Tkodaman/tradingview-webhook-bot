
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from services.market_feed.live_stream import live_trade_manager
print('--- SHADOW POSITIONS ---')
for pid, p in live_trade_manager.shadow_positions.items():
    print(f'{p.symbol} | {p.status}')
print('--- STATS ---')
print(live_trade_manager.daily_stats)

