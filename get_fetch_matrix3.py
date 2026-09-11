with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'async function fetchLiveMatrix\(\) \{[\s\S]*?\} catch', text)
if match:
    print(match.group(0)[:5000])
else:
    print("Not found")
