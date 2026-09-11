with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# We want to replace the exact block:
#                if (balEl && data.account_balance !== undefined) {
#                    lastAlpacaBalance = parseFloat(data.account_balance);
#                    balEl.innerText = $;
#                    const ce = document.getElementById('chartLatestEquity');
#                    if (ce) ce.innerText = $;
#                };
#                }

pattern = re.compile(r'if \(balEl && data\.account_balance !== undefined\).*?\};.*?\}', re.DOTALL)

def replace_fn(match):
    return '''if (balEl && data.account_balance !== undefined) {
                    lastAlpacaBalance = parseFloat(data.account_balance);
                    balEl.innerText = ${parseFloat(data.account_balance).toFixed(2)};
                    const ce = document.getElementById('chartLatestEquity');
                    if (ce) ce.innerText = ${parseFloat(data.account_balance).toFixed(2)};
                }'''

new_text = pattern.sub(replace_fn, text)

# Check for updateChartData error:
# 'updateChartData is not defined at ws.onmessage'
# And 'checkLiveStatus is not defined'

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Replaced syntax block successfully!")
