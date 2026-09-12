with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'Top 15', text, re.IGNORECASE)
for match in matches:
    start = max(0, match.start() - 100)
    end = min(len(text), match.end() + 100)
    print("MATCH AROUND:", text[start:end])
