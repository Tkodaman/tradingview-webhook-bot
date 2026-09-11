with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'Momentum', text, re.IGNORECASE)
if match:
    start = max(0, match.start() - 200)
    end = min(len(text), match.end() + 2000)
    print(text[start:end])
else:
    print("Not found")
