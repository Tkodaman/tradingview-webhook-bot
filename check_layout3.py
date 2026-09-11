with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div[^>]*class="main-grid"[^>]*>', text)
for m in matches:
    print(m.group(0))
    # Print the following 200 characters to see the structure
    print(text[m.end():m.end()+200])
