with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Len line 105: {len(lines[104]) - len(lines[104].lstrip())}")
print(f"Len line 106: {len(lines[105]) - len(lines[105].lstrip())}")
print(f"Len line 107: {len(lines[106]) - len(lines[106].lstrip())}")
print(f"Len line 109: {len(lines[108]) - len(lines[108].lstrip())}")
