with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="panel-header-title">(.*?)</div>', text, flags=re.DOTALL)
for m in matches:
    # Just print ascii chars to avoid crash
    clean = re.sub(r'[^\x00-\x7F]+', ' ', m)
    print(clean.replace('\n', ' ').strip())
