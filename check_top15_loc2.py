with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Top 15', text)]

for idx in matches:
    print(f"\n--- Match at {idx} ---")
    start = max(0, idx - 500)
    end = min(len(text), idx + 10)
    print(text[start:end])
