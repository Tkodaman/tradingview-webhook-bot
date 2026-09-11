with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'top5OpportunitiesWrap', text)]
for idx in matches:
    start = max(0, idx - 100)
    end = min(len(text), idx + 100)
    print("---", text[start:end])

print("-----")

matches2 = [m.start() for m in re.finditer(r'Aktif Açık Pozisyonlar', text)]
for idx in matches2:
    start = max(0, idx - 100)
    end = min(len(text), idx + 100)
    print("---", text[start:end])
