with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,50}main-grid.{0,50}', text)
for m in matches:
    print(m)
