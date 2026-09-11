with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="main-grid".*?>', text)
for m in matches:
    print(m)
