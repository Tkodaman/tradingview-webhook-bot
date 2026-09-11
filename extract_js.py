with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
for i, s in enumerate(scripts):
    with open(f'script_{i}.js', 'w', encoding='utf-8') as sf:
        sf.write(s)
