with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[105:115]):
    print(f"Line {i+106}: {repr(line)}")
