with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
calls = re.findall(r'fetchLiveMatrix.*?', text)
print(calls)
