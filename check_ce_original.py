with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'chartLatestEquity' in line and 'innerText' in line:
        print(f"Line {i+1}: {line.strip()}")
