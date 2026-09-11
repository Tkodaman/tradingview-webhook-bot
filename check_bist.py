with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('Borsa')
start = text.rfind('<div class="', 0, idx)
parent_start = text.rfind('<div class="', 0, start)
print(text[parent_start:idx+50].encode('ascii', 'ignore').decode())
