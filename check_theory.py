with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('class="wallet-bar"')
start = text.find('<!-- MOVED AKTIF', idx)
print(text[start-200:start+200])
