with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Top 15 Alım Isı Haritası', text)]
print("Number of Top 15 in cand_perfect_fixed:", len(matches))
