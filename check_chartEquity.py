with open('templates/dashboard_restored.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'chartEquity.innerText' in line:
        print(f"Line {i+1}: {line.strip()}")
