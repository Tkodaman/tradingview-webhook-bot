with open('dashboard_rebuilt_properly.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'balEl\.innerText = \$\$\{parseFloat\((.*?)\)\.toFixed\(2\)\};', r'balEl.innerText = ${parseFloat(\1).toFixed(2)};', text)
text = re.sub(r'if \(ce\) ce\.innerText = \$\$\{parseFloat\((.*?)\)\.toFixed\(2\)\};', r'if (ce) ce.innerText = ${parseFloat(\1).toFixed(2)};', text)
text = text.replace("}</span></td>", "}")

with open('dashboard_rebuilt_fixed.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed syntax errors in rebuilt file!")
