with open('routers/websocket_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

new_broadcaster = '''
# Background task to send live updates
async def live_data_broadcaster(live_trade_manager: LiveTradeManager):
    last_multiplier = None
    while True:
        try:
            if manager.active_connections:
                prices = live_trade_manager.get_live_prices()
                
                # Check Supervisor Agent Risk Profile
                try:
                    from services.engine.supervisor_agent import supervisor_agent
                    current_mult = supervisor_agent.calculate_dynamic_budget_multiplier(prices)
                    if current_mult != last_multiplier:
                        last_multiplier = current_mult
                        await manager.broadcast({
                            "type": "RISK_UPDATE",
                            "multiplier": current_mult
                        })
                except Exception:
                    pass

                summary = {
'''

text = re.sub(
    r'# Background task to send live updates\s*async def live_data_broadcaster\(live_trade_manager: LiveTradeManager\):\s*while True:\s*try:\s*if manager\.active_connections:\s*prices = live_trade_manager\.get_live_prices\(\)\s*summary = \{',
    new_broadcaster.strip(),
    text,
    flags=re.DOTALL
)

with open('routers/websocket_router.py', 'w', encoding='utf-8') as f:
    f.write(text)
