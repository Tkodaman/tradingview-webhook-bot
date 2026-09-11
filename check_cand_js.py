with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# Print the javascript fetch calls to see if they are broken
fetch_calls = re.findall(r'fetch\(.*?\)', text)
print("Fetch calls:", fetch_calls)

ws_calls = re.findall(r'new WebSocket\(.*?\)', text)
print("WebSocket calls:", ws_calls)
