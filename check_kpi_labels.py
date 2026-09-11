with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="kpi-label">.*?</div>', text)
for m in matches:
    print(m)
