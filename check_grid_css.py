with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import sys
sys.stdout.reconfigure(encoding='utf-8')
idx = text.find('id="top15CryptoBody"')
print(text[max(0, idx-50):idx+250])
