with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'function \w*Chart\w*\(.*?\)', text)
for m in matches:
    print(m)
