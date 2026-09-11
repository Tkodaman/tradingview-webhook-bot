with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.DOTALL)
js = scripts[1]
lines = js.split('\n')
for i in range(330, 345):
    if i < len(lines):
        print(f"Line {i+1}: {lines[i]}")
