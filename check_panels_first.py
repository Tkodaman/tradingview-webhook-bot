with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="panel.*?>(.*?)</div>', text, re.DOTALL)
for m in matches[:5]:
    print("Found panel snippet:", m.strip()[:60].replace('\n', ' '))
