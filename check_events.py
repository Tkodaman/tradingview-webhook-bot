with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
onload_matches = re.findall(r'window\.onload', text)
dom_matches = re.findall(r'DOMContentLoaded', text)

print("onload matches:", len(onload_matches))
print("DOMContentLoaded matches:", len(dom_matches))
