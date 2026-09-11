with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'balEl.innerText' in line:
        print(f"Working Line {i}: {repr(line)}")
