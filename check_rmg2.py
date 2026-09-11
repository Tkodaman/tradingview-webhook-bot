with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('function fetchLiveMatrix')
if idx != -1:
    func_text = text[idx:idx+1500]
    print(re.findall(r'render.*', func_text))
