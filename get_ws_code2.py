with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
ws_code = re.search(r'const wsUrl =.*?};', text, re.DOTALL)
if ws_code:
    print("Found ws code!")
    print(ws_code.group(0)[:500])
