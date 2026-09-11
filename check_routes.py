with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'@app\.get\(["\'](.*?)["\']\)', text)
print("GET routes in main.py:", matches)
