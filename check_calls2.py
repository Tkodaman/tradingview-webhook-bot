with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'fetchLiveMatrix\(\);?', text)
print("fetchLiveMatrix calls:", len(matches))
matches2 = re.findall(r'connectWebSocket\(\);?', text)
print("connectWebSocket calls:", len(matches2))
