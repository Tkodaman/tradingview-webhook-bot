with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
js = re.search(r'<script>(.*)</script>', text, re.DOTALL)
if js:
    code = js.group(1)
    lines = code.split('\n')
    print("Last 15 lines:")
    for line in lines[-15:]:
        print(line)
