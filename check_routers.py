with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'include_router\((.*?)\)', text)
print("Routers included:", matches)
