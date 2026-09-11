import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('MAIN DASHBOARD LAYOUT')
start = text.find('<div style="display: flex; gap: 24px', idx)
end = text.find('<!-- END MAIN DASHBOARD GRID -->', start)

if start != -1 and end != -1:
    content = text[start:end]
    matches = re.finditer(r'<div[^>]*style="flex:[^"]*"', content)
    for m in matches:
        print(m.group(0))
        print(re.sub(r'[^\x00-\x7F]+', ' ', content[m.end():m.end()+150]))
