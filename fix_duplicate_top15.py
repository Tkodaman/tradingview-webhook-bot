import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'top5OpportunitiesWrap', text)]

print(f"Number of top5OpportunitiesWrap: {len(matches)}")

start = matches[0]
end = matches[1]

print("Deleting from", start, "to", end)

text = text[:start] + text[end:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
