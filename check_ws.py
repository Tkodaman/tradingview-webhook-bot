with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'ws\.onmessage\s*=\s*(function\s*\([^)]*\)|.*?=>)\s*\{', text)
for match in matches:
    start_idx = match.start()
    end_idx = start_idx + 1500
    print(text[start_idx:end_idx])
