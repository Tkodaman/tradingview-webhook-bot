with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="markets-container(.*?)"', text)
for match in matches:
    print(f"Match: {match.group(0)}")
