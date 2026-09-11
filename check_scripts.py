with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.finditer(r'<script>', text)
for m in matches:
    print("Found script at:", m.start())
