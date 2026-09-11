import re
with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

ws_line = re.search(r'const wsUrl = .*?;', text)
if ws_line:
    print(ws_line.group(0))
