with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<!-- END MAIN DASHBOARD GRID -->', text)
for m in matches:
    print(text[m.start()-50:m.end()+150])
