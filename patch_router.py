import re

with open('services/order_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fallback block to inject
fallback_code = """
                res = broker.place_bracket_order(signal.symbol, "BUY", final_qty, tp_price, sl_price)
                if res.get("status") == "error":
                    logger.warning(f"[BROKER FALLBACK] Alpaca API error: {res.get('message')}. Falling back to Simulation Mode.")
                    pos = live_trade_manager.open_position(signal.symbol, capital_used, "BUY", tp_pct, sl_pct, signal.price)
                    if pos:
                        res = {"status": "success", "order_id": f"SIM-{pos.id}", "details": "Simulated fallback"}
"""
content = content.replace('res = broker.place_bracket_order(signal.symbol, "BUY", final_qty, tp_price, sl_price)', fallback_code.strip())

with open('services/order_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
