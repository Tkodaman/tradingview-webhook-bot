with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
# Remove the stray }; that comes after lastAlpacaBalance
html = html.replace('if (ce) ce.innerText = $;\n};', 'if (ce) ce.innerText = $;')
html = html.replace('if (ce) ce.innerText = $;\n                };', 'if (ce) ce.innerText = $;')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
