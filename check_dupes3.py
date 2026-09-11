with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Number of renderMarketGroup in pure_js:", len(re.findall(r'renderMarketGroup', text)))
