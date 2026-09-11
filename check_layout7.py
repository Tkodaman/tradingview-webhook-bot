import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'top5OpportunitiesWrap', text)]
idx_top = matches[0]

matches2 = [m.start() for m in re.finditer(r'Aktif Açık Pozisyonlar & Kâr/Zarar Takibi', text)]
idx_aktif = matches2[0]

print("Top 15 is at:", idx_top)
print("Aktif is at:", idx_aktif)

start = max(0, idx_top - 100)
end = min(len(text), idx_aktif + 200)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
