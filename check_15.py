with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,30}15.{0,30}', text)
for m in set(matches):
    print(m)
