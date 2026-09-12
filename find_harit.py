with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<h[1-4].*?Haritas.*?/h[1-4]>', text, re.DOTALL | re.IGNORECASE)
for match in matches:
    print("Found header:", match.group(0))
