with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'\.ticker-grid.*?\}', text, re.DOTALL)
for match in matches:
    print(match.group(0))
