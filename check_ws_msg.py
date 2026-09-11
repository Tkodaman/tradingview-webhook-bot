with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
onmessage_block = re.search(r'ws\.onmessage\s*=\s*\(event\)\s*=>\s*\{.*?\}', text, re.DOTALL)
if onmessage_block:
    print("Found onmessage block!")
    print(onmessage_block.group(0)[:500])
else:
    print("NO onmessage BLOCK FOUND!")
