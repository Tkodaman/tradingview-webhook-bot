with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
matches = re.finditer(r'function\s+\w+\s*\([^)]*\)\s*\{|=>\s*\{', js)
for m in matches:
    print(f"Function started at index {m.start()}: {m.group(0).strip()}")
