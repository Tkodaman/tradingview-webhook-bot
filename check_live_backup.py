with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('function fetchLiveMatrix')
func = text[idx-10:idx+30]
print(func)
