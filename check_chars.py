with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
weird = set(re.findall(r'[^\x00-\x7F]', text))
for c in weird:
    try:
        print(repr(c).encode('ascii', errors='backslashreplace').decode('ascii'))
    except:
        pass
