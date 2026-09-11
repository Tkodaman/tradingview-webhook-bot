with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('// --- NEW JS ---')
bottom_js = text[idx:]

# Print the context around "const res = await fetch('/api/positions/active');"
context = bottom_js[bottom_js.find('const res = await fetch'):bottom_js.find('const res = await fetch')+500]
print(context)
