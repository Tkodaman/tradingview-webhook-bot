with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('class="header-section"')
print(text[max(0, idx-100):idx+100])
