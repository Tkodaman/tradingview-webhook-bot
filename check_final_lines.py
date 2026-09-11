with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
import sys
sys.stdout.reconfigure(encoding='utf-8')
for i in range(max(0, 1990), min(len(lines), 2060)):
    print(f"{i+1}: {lines[i].rstrip()}")
