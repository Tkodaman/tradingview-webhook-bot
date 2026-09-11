with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
print("Looking for any width constraint on panel or container...")
matches = re.finditer(r'(width|max-width):\s*(\d+)px', text)
for m in matches:
    print(text[m.start()-50:m.end()+20])
