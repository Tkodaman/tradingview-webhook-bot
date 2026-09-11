with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
body_start = text.find('<body>')
print(text[body_start:body_start+800].encode('ascii', 'ignore').decode())
