with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<h2 class="panel-header-title">.*?Top 15 Alım Isı Haritası.*?</h2>', text, re.DOTALL)
for match in matches:
    idx = text.rfind('<div', 0, match.start())
    print(text[idx:idx+300])
