with open('services/order_router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'broker.place_bracket_order' in line or 'except' in line or 'broker_res' in line:
        start = max(0, i-2)
        end = min(len(lines), i+5)
        print(f"--- line {i+1} ---")
        for j in range(start, end):
            if j < len(lines):
                print(f"{j+1}: {lines[j].rstrip()}")
