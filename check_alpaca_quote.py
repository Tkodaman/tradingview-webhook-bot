with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'def.*?quote', text, re.IGNORECASE)
for match in matches:
    print(match.group(0))
