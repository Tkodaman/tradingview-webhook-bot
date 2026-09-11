with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

match = re.search(r'const cryptoHtml = ', text, re.IGNORECASE)
if match:
    start = max(0, match.start() - 200)
    end = min(len(text), match.end() + 2000)
    print(text[start:end])
else:
    print("Not found, searching for 'cryptoList.map'")
    match2 = re.search(r'cryptoList\.map', text, re.IGNORECASE)
    if match2:
        start = max(0, match2.start() - 200)
        end = min(len(text), match2.end() + 2000)
        print(text[start:end])
