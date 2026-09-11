with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
print("Has wsUrl:", 'const wsUrl' in text)
print("Has Crypto window:", 'Kripto Piyasas' in text or 'market-window-crypto' in text)
print("Has script tags:", text.count('<script>'))
