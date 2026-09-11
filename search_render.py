with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'function renderMarketGroup' in line:
        start = max(0, i)
        end = min(len(lines), i+60)
        print(f"--- renderMarketGroup ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
