with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '/live-matrix' in line or 'def live_market_matrix' in line:
        print(f"{i+1}: {line.strip()}")
