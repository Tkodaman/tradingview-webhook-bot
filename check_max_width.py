with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'max-width:\s*([^;]+);', text)
for m in matches:
    print(m.group(0))
