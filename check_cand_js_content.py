with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
if scripts:
    js = scripts[0]
    print(js[:500])
    print("JS length:", len(js))
