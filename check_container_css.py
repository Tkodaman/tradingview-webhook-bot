with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'\.(container|wrapper|layout)[^\{]*\{([^\}]*)\}', text)
for m in matches:
    print(m.group(0))
