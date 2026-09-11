with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'templates.*?\.html', text)
for m in matches:
    print(m)
