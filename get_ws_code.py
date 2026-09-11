with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
ws_code = re.search(r'// ================================================================\s*// 🚀 WEBSOCKET CANLI PİYASA AKIŞI(.*?)// LLM blink animation', text, re.DOTALL)
if ws_code:
    code = ws_code.group(1)
    print("WebSocket code length:", len(code))
    print(code[:200])
else:
    print("Not found in dashboard.html")
