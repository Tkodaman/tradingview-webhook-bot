with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'[^]*\[^]*', text)
print("Found", len(matches), "template literals.")

# Check for stray braces
m2 = re.findall(r'}\s*;', text)
print("Found", len(m2), "stray braces with semi.")

