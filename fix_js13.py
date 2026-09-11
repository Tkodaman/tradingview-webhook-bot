with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# I will just take out the }</span></td>
text = text.replace("}</span></td>", "}")

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Removed HTML tags from JS!")
