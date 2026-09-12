with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'class="panel(.*?)<h2 class="panel-header-title', text, re.DOTALL)
for match in matches:
    print(f"--- MATCH ---")
    print(match.group(0)[:150])
