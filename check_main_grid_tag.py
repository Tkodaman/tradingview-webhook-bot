with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'<div class="main-grid"([^>]*)>', text)
if match:
    print(match.group(0))
