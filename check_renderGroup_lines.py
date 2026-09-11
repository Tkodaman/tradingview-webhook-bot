with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "function renderMarketGroup" in line:
        print(f"Start at: {i}")
        for j in range(i, i+50):
            print(f"{j+1}: {lines[j].strip()}")
        break
