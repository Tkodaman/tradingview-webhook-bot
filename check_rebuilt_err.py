with open('dashboard_rebuilt_properly.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Print line 1450 to 1475 to see if there are syntax errors!
for i, line in enumerate(text.splitlines()[1455:1475]):
    print(i+1456, line)
