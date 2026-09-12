with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()
if "rsi_climbed_from_40" in text:
    print("SUCCESS: RSI logic is in the file")
else:
    print("FAILED: RSI logic not in the file")
