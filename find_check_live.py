with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'function checkLiveStatus\(\).*?\}', text, flags=re.DOTALL)
if match:
    print("Found checkLiveStatus:")
    print(match.group(0)[:500])
else:
    print("Not found.")
