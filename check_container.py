with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="markets-container(.*?)</div>\s*<!--', text, re.DOTALL)
for match in matches:
    print(match.group(0)[:300])
