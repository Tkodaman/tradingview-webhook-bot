with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<h2 class="panel-header-title">.*?</h2>', text, re.DOTALL)
output = []
for match in matches:
    output.append(match.group(0).replace('\n', ' '))

with open('debug_h2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
