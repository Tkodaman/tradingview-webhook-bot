with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# Fix backticks if missing in cand_5b4e9.html
text = re.sub(r'balEl\.innerText = \$\$\{parseFloat\((.*?)\)\.toFixed\(2\)\};', r'balEl.innerText = ${parseFloat(\1).toFixed(2)};', text)
text = re.sub(r'if \(ce\) ce\.innerText = \$\$\{parseFloat\((.*?)\)\.toFixed\(2\)\};', r'if (ce) ce.innerText = ${parseFloat(\1).toFixed(2)};', text)
text = text.replace("}</span></td>", "}")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Dashboard overwritten with cand_5b4e9.html and syntax fixed!")
