with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('output.txt', 'wb') as f:
    for i, line in enumerate(lines[105:115]):
        f.write(f"Line {i+106}: {repr(line)}\n".encode('utf-8'))
