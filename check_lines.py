with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[100:115]):
    print(f"{i+101}: {repr(line)}")
