with open('routers/position_router.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'get_active_positions' in line:
        start = max(0, i)
        end = min(len(lines), i+60)
        print(f"--- get_active_positions ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
