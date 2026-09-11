import os
import re

for filename in os.listdir('templates'):
    if filename.endswith('.html'):
        path = os.path.join('templates', filename)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            if 'kutucuk' in text.lower() or 'grid' in text.lower() or 'box' in text.lower():
                # Let's see if we can find something related to top15CryptoBody
                idx = text.find('top15CryptoBody')
                if idx != -1:
                    print(f"Found in {filename}")
