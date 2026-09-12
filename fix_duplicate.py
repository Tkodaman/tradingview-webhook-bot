with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('rsi_history = {}\nrsi_history = {}', 'rsi_history = {}')
with open('routers/market_router.py', 'w', encoding='utf-8') as f:
    f.write(text)
