import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Top 15', text)]

for idx in matches:
    sys.stdout.buffer.write(f"\n--- Match at {idx} ---\n".encode('utf-8'))
    start = max(0, idx - 500)
    end = min(len(text), idx + 10)
    sys.stdout.buffer.write(text[start:end].encode('utf-8'))
