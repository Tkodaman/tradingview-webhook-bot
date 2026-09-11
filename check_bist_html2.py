with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('BORSA')
if idx != -1:
    print(text[idx-150:idx+150].encode('ascii', 'ignore').decode())
