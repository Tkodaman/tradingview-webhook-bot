with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'id="gridNasdaq"' in line or 'id="gridKripto"' in line or 'id="gridBist"' in line:
        print(f"{i+1}: {line.strip()}")
