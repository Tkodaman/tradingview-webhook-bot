with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'\.market-closed\s*\{[^}]*\}', text)
if match:
    print(match.group(0))
else:
    print("CSS .market-closed NOT FOUND")
