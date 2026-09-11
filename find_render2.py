with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'function renderMarketGroup', text, re.IGNORECASE)
if match:
    start = max(0, match.start() - 500)
    end = min(len(text), match.start())
    print(text[start:end])
else:
    print("Not found")
