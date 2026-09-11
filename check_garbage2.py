import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('overflow-x: auto;')
print("Starting near index", idx)

import sys
sys.stdout.buffer.write(text[idx:idx+1500].encode('utf-8'))
