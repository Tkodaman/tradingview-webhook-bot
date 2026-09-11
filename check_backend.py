with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'def \w*ortfoy\w*|def \w*balance\w*|def \w*distribution\w*', text, re.IGNORECASE)
print("Endpoints:", matches)
