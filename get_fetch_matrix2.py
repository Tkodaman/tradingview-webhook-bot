with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'function fetchLiveMatrix\(\) \{[\s\S]*?async function fetchSummary', text)
if match:
    print(match.group(0)[:5000])
else:
    print("Not found")
