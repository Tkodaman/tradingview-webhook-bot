import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Top 15', text)]
idx = matches[0]

start = idx
end = start + 800

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
