with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<h[1-4].*?class=".*?title.*?>(.*?)</h[1-4]>', text, re.IGNORECASE)
for match in matches:
    try:
        print("Match:", match.group(1).strip()[:100])
    except:
        pass

matches2 = re.finditer(r'<div class="window-title">(.*?)</div>', text, re.IGNORECASE | re.DOTALL)
for match in matches2:
    try:
        print("Match Window:", match.group(1).strip()[:100])
    except:
        pass
