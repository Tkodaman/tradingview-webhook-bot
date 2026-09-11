with open('services/order_router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'trading_mode' in line or 'def process_order' in line:
        start = max(0, i)
        end = min(len(lines), i+15)
        print(f"--- line {i+1} ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
