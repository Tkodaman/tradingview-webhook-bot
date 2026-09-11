with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('max-width:60%')
if idx != -1:
    print(text[max(0, idx-150):idx+150])
