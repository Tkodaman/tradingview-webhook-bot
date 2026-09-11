with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="market-window([^"]*)"(.*?)(<div class="ticker-grid")', text, re.DOTALL)
for m in matches:
    cls = m.group(1).strip()
    if cls == 'market-window-nasdaq':
        header_content = m.group(2)
        print(re.sub(r'[^\x00-\x7F]+', ' ', header_content))
