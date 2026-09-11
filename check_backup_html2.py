import re

with open('backup_html_structure.txt', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('15')
print("Found 15 at:", idx)

import sys
sys.stdout.buffer.write(text[max(0, idx-200):idx+200].encode('utf-8'))
