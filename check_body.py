with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.search(r'body\s*\{([^\}]*)\}', text)
if matches:
    print(f"body: {matches.group(1).strip()}")
