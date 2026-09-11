with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('Kripto Terminali')
parent = text.rfind('<div class="panel"', 0, idx)
print(text[parent:parent+500].encode('ascii', 'ignore').decode())
