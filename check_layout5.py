import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'top5OpportunitiesWrap', text)]
print(f"Number of top5OpportunitiesWrap remaining: {len(matches)}")

idx = matches[0]
start = max(0, idx - 200)
end = min(len(text), idx + 200)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
