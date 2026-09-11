import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('MAIN DASHBOARD LAYOUT')
start = text.rfind('<div', 0, idx)
print(re.sub(r'[^\x00-\x7F]+', ' ', text[start:idx+300]))
