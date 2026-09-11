with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.finditer(r'<script(.*?)</script>', text, re.DOTALL)
for i, m in enumerate(matches):
    length = m.end() - m.start()
    print(f"Script {i} at {m.start()} length {length}")
