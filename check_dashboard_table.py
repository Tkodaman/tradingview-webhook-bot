with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Print around 'target_profit_price'
idx = text.find('target_profit_price')
if idx != -1:
    print(text[max(0, idx-200):min(len(text), idx+200)])
