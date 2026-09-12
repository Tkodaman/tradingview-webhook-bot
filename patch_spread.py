with open('services/order_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

new_spread = '''
    if action_clean in ["BUY", "LONG", "SELL", "SHORT"]:
        try:
            from services.risk_engine.missing_agents import spread_guard
            from services.market_feed.live_stream import live_trade_manager
            is_spread_ok = spread_guard.check_spread(signal.symbol, live_trade_manager.market_prices)
        except Exception:
            pass
            
'''

text = re.sub(
    r'if action_clean in \["BUY", "LONG"\]:',
    new_spread.strip() + '\n    if action_clean in ["BUY", "LONG"]:',
    text,
    count=1,
    flags=re.DOTALL
)

with open('services/order_router.py', 'w', encoding='utf-8') as f:
    f.write(text)
