import re
with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Let's see the divs
divs = re.findall(r'<div class="([^"]+)"', text)
counts = {}
for d in divs:
    c = d.split()[0]
    counts[c] = counts.get(c, 0) + 1

print("Div classes:", sorted(counts.items(), key=lambda x: -x[1])[:30])

# Let's see the scripts
print("Has wsUrl:", 'wsUrl' in text)
print("Has onmessage:", 'onmessage' in text)
