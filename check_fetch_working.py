with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'fetch\([\'](.*?)[\']\)', text)
print("Fetch calls in working_backup:", set(matches))
