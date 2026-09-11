import sys

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Top 15', text)]
for idx in matches:
    start = max(0, idx - 100)
    end = min(len(text), idx + 100)
    sys.stdout.buffer.write(text[start:end].encode('utf-8'))
    print("\n------------------\n")
