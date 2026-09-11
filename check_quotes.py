with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'\\"', text)
print("Number of literal quote escapes:", len(matches))
