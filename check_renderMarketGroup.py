with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'function renderMarketGroup\([\s\S]*?\}', text)
if match:
    print(match.group(0)[:2000])
else:
    print("Not found")
