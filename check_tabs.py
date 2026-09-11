with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'filter-tabs', text)
for m in matches:
    print(f"Found filter-tabs at {m.start()}")
