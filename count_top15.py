with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'Top 15', text)
print("Number of Top 15 strings:", len(matches))
