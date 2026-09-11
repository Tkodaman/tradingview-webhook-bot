with open('services/order_router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'live_trade_manager.open_position' in line:
        start = max(0, i-5)
        end = min(len(lines), i+15)
        print(f"--- line {i+1} ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
