with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<button[^>]+Kapat[^>]*>', text, re.IGNORECASE)
for m in matches:
    print(m.group(0))

matches = re.finditer(r'fetchPositions', text, re.IGNORECASE)
for m in matches:
    print(f"fetchPositions found at {m.start()}")
