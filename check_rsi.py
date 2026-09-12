with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'rsi\s*[<>=]+\s*\d+', text, re.IGNORECASE)
for match in matches:
    print(match.group(0))
