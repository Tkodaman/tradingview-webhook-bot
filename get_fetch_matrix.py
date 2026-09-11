with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'function fetchLiveMatrix', text, re.IGNORECASE)
if match:
    start = match.start()
    end = min(len(text), text.find('// 4. FETCH ALGORITHMIC STATS', start))
    print(text[start:end])
else:
    print("Not found")
