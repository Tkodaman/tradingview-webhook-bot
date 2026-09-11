with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# check for missing backticks
if re.search(r'balEl\.innerText = \$\$\{parseFloat', text):
    print("Found missing backtick for balEl")
else:
    print("balEl backticks OK or not found")
    
if '}</span></td>' in text:
    print("Found }</span></td> syntax error")
else:
    print("span syntax error not found")
