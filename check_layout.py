with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'Kripto Piyasas' in line or 'BIST 100/30' in line or 'NASDAQ Mega-Cap' in line:
        start = max(0, i-5)
        end = min(len(lines), i+2)
        print(f"--- Line {i+1} Context ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
