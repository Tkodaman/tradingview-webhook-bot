with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
ws_calls = re.findall(r'new WebSocket\(.*?\)', text)
print("WebSocket calls in current stable dashboard:", ws_calls)
