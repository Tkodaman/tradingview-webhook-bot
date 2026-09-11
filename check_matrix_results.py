with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'matrix_results\.append\(\{([\s\S]*?)\}\)', text)
if match:
    print(match.group(1))
