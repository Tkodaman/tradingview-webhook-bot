import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('MAIN CONTENT (Chart Removed)')
start = text.find('<div style="flex: 1 1 100%', idx)
print(re.sub(r'[^\x00-\x7F]+', ' ', text[start:start+300]))
