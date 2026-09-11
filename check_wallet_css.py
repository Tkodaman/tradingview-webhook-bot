with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.search(r'\.wallet-bar\s*\{([^\}]*)\}', text)
if matches:
    print(".wallet-bar:", matches.group(1).strip())
