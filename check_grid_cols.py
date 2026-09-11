with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'([\.#a-zA-Z0-9_-]+)\s*\{[^}]*grid-template-columns:[^;]+;', text)
for m in matches:
    print(m.group(0))
