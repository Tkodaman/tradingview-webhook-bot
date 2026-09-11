with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.search(r'\.header-section\s*\{([^\}]*)\}', text)
if matches:
    print(".header-section:", matches.group(1).strip())
