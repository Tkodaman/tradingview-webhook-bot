with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.search(r'\.main-grid\s*\{([^\}]*)\}', text)
if matches:
    print(f"main-grid: {matches.group(1).strip()}")
