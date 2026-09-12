with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('output2.txt', 'wb') as f:
    for i, line in enumerate(lines[90:108]):
        f.write(f"Line {i+91}: {repr(line)}\n".encode('utf-8'))
