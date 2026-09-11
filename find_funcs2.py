with open('templates/cand_perfect2.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'function \w+\(.*?\)', text[text.find('<script>'):])
print("Functions found in cand_perfect2:", set(matches))
