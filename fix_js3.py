import re

with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'if \(balEl && data\.account_balance !== undefined\) \{.*?balEl\.innerText = \$.*?\n.*?const ce = document.*?if \(ce\) ce.*?\};.*?\}'
new_block = '''if (balEl && data.account_balance !== undefined) {
                    lastAlpacaBalance = parseFloat(data.account_balance);
                    balEl.innerText = ${parseFloat(data.account_balance).toFixed(2)};
                    const ce = document.getElementById('chartLatestEquity');
                    if (ce) ce.innerText = ${parseFloat(data.account_balance).toFixed(2)};
                }'''

match = re.search(pattern, text, re.DOTALL)
if match:
    # Need to replace  with $ for actual JS template literal because Python format strings might not be involved here, but I used $$ so parseFloat isn't interpreted as bash var? No, this is python. I'll just use $
    new_block = new_block.replace('', '$')
    text = text[:match.start()] + new_block + text[match.end():]
    with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced successfully via regex!")
else:
    print("Regex failed to match!")
