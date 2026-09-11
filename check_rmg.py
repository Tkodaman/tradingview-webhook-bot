with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'renderMarketGroup\([^)]*\)', text)
for m in matches:
    print(m)
