import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('MAIN DASHBOARD LAYOUT')
start = text.find('<div style="display: flex;', idx)
print(text[start:start+150])
