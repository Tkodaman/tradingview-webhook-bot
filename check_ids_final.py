with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'<div[^>]*class="[^"]*market-window[^"]*"[^>]*id="([^"]+)"', text)
print("Market window IDs:", matches)

matches = re.findall(r'renderMarketGroup\(\'([^\']+)\'', text)
print("renderMarketGroup calls with IDs:", matches)
