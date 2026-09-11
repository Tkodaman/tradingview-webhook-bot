with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
scripts = re.findall(r'<script(.*?)</script>', text, re.DOTALL)
print("Number of scripts:", len(scripts))
for i, s in enumerate(scripts):
    print(f"Script {i} length: {len(s)}")
