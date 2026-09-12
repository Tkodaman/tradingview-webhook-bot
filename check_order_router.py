with open('services/order_router.py', 'r', encoding='utf-8') as f:
    text = f.read()
if "from services.broker.factory import get_broker" in text.split("if settings.trading_mode in [\"LIVE\", \"PAPER\"]")[1]:
    print("order_router is NOT patched")
else:
    print("order_router IS patched")
