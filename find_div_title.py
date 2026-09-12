with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="panel-header-title">.*?</div>', text, re.DOTALL)
output = []
for match in matches:
    output.append(match.group(0).replace('\n', ' '))

with open('debug_div_title.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
