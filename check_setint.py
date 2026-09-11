with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'setInterval\(', text)
print("setInterval count:", len(matches))
