with open(r'_archive\dashboard_old.html', 'r', encoding='utf-16') as f:
    text = f.read()
import re
idx = text.find('fetchPositions() {')
if idx != -1:
    print(text[idx:idx+1500])
