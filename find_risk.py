with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'Sentry|Risk', text, re.IGNORECASE)
for match in matches:
    start = max(0, match.start() - 50)
    end = min(len(text), match.end() + 50)
    snippet = text[start:end].replace('\n', ' ')
    print(f"Match: {snippet}")
