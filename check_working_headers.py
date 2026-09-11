with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="panel-header.*?>(.*?)</div>', text, re.DOTALL)
for i, m in enumerate(matches):
    print(f"Panel {i}: {m.strip().encode('ascii', 'ignore').decode('ascii')[:50]}")
