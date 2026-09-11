with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
wsUrl_matches = re.findall(r'(const|let|var)\s+wsUrl\s*=', text)
print("wsUrl matches:", len(wsUrl_matches))

pnlChart_matches = re.findall(r'(const|let|var)\s+pnlChart\s*=', text)
print("pnlChart matches:", len(pnlChart_matches))
