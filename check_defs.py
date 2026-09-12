with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'^[ \t]*def .*?:', text, re.MULTILINE)
for match in matches:
    print(repr(match.group(0)))
