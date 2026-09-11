with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.search(r'\.panel\s*\{([^\}]*)\}', text)
if matches:
    print(f".panel: {matches.group(1).strip()}")
