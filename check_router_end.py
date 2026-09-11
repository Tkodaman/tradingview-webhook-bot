with open('routers/engine_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'/live-matrix', text, re.IGNORECASE)
if match:
    start = max(0, match.start() + 2000)
    end = min(len(text), match.end() + 4500)
    print(text[start:end])
else:
    print("Not found")
