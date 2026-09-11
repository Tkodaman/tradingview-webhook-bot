with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'function updateClock', text)
for m in matches:
    start = m.start()
    end = text.find('}', start)
    print(text[start:end+1])
