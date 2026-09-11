with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer('Aktif A', text)]
for m in matches:
    print(f"Index {m}: {text[m-50:m+50]}")
