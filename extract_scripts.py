with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

import re
# extract all script tags
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    with open(f'script_{i}.js', 'w', encoding='utf-8') as sf:
        sf.write(s)
print(f"Extracted {len(scripts)} scripts")
