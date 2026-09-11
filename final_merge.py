with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    dash = f.read()

import re
match = re.search(r'(const wsUrl =.*?ws\.onclose =.*?\n\s*};)', dash, re.DOTALL)
ws_block = match.group(1)

with open('templates/cand_5b4e9_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    cand = f.read()

cand = cand.replace('// LLM blink animation', ws_block + '\n\n// LLM blink animation')

# Fix  syntax errors
cand = re.sub(r'\$\$\{', '${', cand)
cand = re.sub(r'toFixed\(2\)\};', 'toFixed(2)};', cand)
cand = cand.replace("}</span></td>", "}")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(cand)

print("SUCCESSFULLY merged WS block and fixed JS tags into templates/dashboard.html")
