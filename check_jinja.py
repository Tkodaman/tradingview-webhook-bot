with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = set(re.findall(r'\{\{.*?\}\}', text))
for m in matches:
    print(m)
