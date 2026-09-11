with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'function renderMarketGroup.*?\{.*?(<tbody>.*?</tbody>).*?\}', text, flags=re.DOTALL)
if match:
    print(match.group(1))
