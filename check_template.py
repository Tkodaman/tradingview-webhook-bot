with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
matches = re.findall(r'[^\w]?\$\$\{', js)
print("Matches for template variables:", len(matches))
