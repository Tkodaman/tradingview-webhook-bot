with open('services/broker/alpaca_bridge.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'def place_bracket_order' in line:
        start = max(0, i)
        end = min(len(lines), i+30)
        print(f"--- line {i+1} ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
