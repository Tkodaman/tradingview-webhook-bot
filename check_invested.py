import os, sys
sys.path.append(os.getcwd())
from services.market_feed.live_stream import live_trade_manager
print(f'total_invested: {sum(p.nominal_value for p in live_trade_manager.positions.values() if (p.status == "OPEN" or (p.status == "PENDING_BROKER" and p.broker_order_id)) and p.market == "CRYPTO")}')
