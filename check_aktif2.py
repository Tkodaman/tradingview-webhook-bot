with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer('Aktif A', text)]
for m in matches:
    clean = re.sub(r'[^\x00-\x7F]+', ' ', text[m-50:m+50])
    print(f"Index {m}: {clean}")
