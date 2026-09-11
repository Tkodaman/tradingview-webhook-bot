with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'function updateTime\(\)\s*\{[\s\S]*?\}', text)
for m in matches:
    print(f"Found updateTime at {m.start()}")
    text = text[:m.start()] + 'function updateTime() { /* replaced by updateClockUI */ }' + text[m.end():]

# Let's also find the setInterval for updateTime if it exists
text = text.replace('setInterval(updateTime, 1000);', '// setInterval(updateTime, 1000); // replaced')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Removed old clock logic.")
