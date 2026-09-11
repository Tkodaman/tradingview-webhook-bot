with open('templates/cand_perfect2.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
js = re.search(r'<script>(.*)</script>', text, re.DOTALL)
if js:
    code = js.group(1)
    print("cand_perfect2 Brackets:", code.count('{'), code.count('}'))
