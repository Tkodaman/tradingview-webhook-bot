with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,100}15.{0,100}', text)
for i, m in enumerate(set(matches)):
    clean = re.sub(r'[^\x00-\x7F]+', ' ', m)
    print(f"Match {i}: {clean.replace(chr(10), ' ').strip()}")
