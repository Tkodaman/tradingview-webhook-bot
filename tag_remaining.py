with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# We already tagged a1, a4, a7.
# We need to tag a2, a3, a5, a6.

reps = [
    (r'(<span>💼</span>\s*)(Aktif Açık Pozisyonlar & Kâr/Zarar Takibi)', r'\1(a2) \2'),
    (r'(<span>🛡️</span>\s*)(Algoritmik Risk & Bütçe Yönetimi)', r'\1(a3) \2'),
    (r'(<span style="color:#10b981;">🇹🇷</span>\s*)(TR BIST Terminali)', r'\1(a5) \2'),
    (r'(<span style="color:#3b82f6;">🇺🇸</span>\s*)(US NASDAQ Terminali)', r'\1(a6) \2')
]

for pat, repl in reps:
    text, count = re.subn(pat, repl, text, flags=re.IGNORECASE)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

