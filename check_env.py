with open('.env', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for line in lines:
    if 'TRADING_MODE' in line or 'ALPACA' in line:
        print(line.strip())
