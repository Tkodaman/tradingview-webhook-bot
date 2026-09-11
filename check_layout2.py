with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Check grid class
matches = re.finditer(r'<div class="([^"]*grid[^"]*)"', text)
for m in matches:
    print(f"Grid div found: {m.group(1)}")

# Find terminal containers
t_matches = re.finditer(r'Terminali', text)
for m in t_matches:
    start = max(0, m.start() - 100)
    print(f"Terminal context: {text[start:m.start()+50]}")
    break
