with open('services/engine/auto_runner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'process_order' in line:
        start = max(0, i-5)
        end = min(len(lines), i+5)
        print(f"--- line {i+1} ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
