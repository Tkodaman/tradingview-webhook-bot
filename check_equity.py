with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,20}EQUITY.{0,20}', text)
for m in matches:
    print(m)
