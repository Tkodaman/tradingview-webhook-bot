with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="market-window market-window-crypto">[\s\S]*?</div>\s*</div>', text)
if matches:
    print(matches[0][:500].encode('ascii', 'ignore').decode('ascii'))
else:
    print("No matches")
