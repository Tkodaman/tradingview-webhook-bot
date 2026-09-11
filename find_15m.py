import os
import re

for filename in os.listdir('templates'):
    if filename.endswith('.html'):
        with open(os.path.join('templates', filename), 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            if '15 Momentum' in text or '15 momentum' in text or 'Top 15' in text:
                print(f"Found in {filename}")
