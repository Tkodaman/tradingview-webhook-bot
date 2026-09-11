with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Get context around all occurrences
for match in re.finditer(r'fetchLiveMatrix', text):
    start = max(0, match.start() - 50)
    end = min(len(text), match.end() + 50)
    print("Match:")
    print(text[start:end].replace('\n', ' '))
