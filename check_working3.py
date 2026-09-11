with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'return idx === 0 \? \'Start\' : (.*);', text)
print("Matches in working backup:", matches)

matches2 = re.findall(r'borderColor = \'rgba', text)
print("Matches 2 in working backup:", len(matches2))
