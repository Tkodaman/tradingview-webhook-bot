with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div[^>]*id="([^"]+)"[^>]*>', text)
print("IDs:", matches[:20])
