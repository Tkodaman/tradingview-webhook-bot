with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="two-col-grid"', text)
for m in matches:
    print(text[m.start()-20:m.start()+200])

log_match = re.search(r'id="[^"]*Log"', text)
if log_match:
    print(f"Found log id: {log_match.group(0)}")
