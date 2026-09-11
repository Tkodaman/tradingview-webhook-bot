with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('function fetchLiveMatrix')
func = text[idx:idx+1500]
print(func.encode('ascii', 'ignore').decode('ascii'))
