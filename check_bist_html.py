with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
idx = text.find('BORSA')
if idx != -1:
    start = text.rfind('<div', 0, idx)
    parent_start = text.rfind('<div', 0, start)
    grand_start = text.rfind('<div', 0, parent_start)
    print(text[grand_start:idx+50].encode('ascii', 'ignore').decode())
