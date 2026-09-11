with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

import sys
sys.stdout.reconfigure(encoding='utf-8')

for i in range(max(0, 2030), min(len(lines), 2050)):
    print(f"{i+1}: {lines[i].strip()}")
