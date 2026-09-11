with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'return idx === 0' in line:
        print(f"Line {i}: {line.strip().encode('utf-8')}")
