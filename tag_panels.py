import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = [
    (r'(<div class="header-title">.*?)(TRADINGVIEW)', r'\1(A1) \2'),
    (r'(<h2 class="panel-header-title">.*?)(Açık Pozisyonlar & Canlı Takip)', r'\1(A2) \2'),
    (r'(<h2 class="panel-header-title">.*?)(Risk Yönetimi & Otonom Sentry)', r'\1(A3) \2'),
    (r'(<div class="window-title">.*?)(Kripto Piyasası)', r'\1(A4) \2'),
    (r'(<div class="window-title">.*?)(TR BIST 100/30)', r'\1(A5) \2'),
    (r'(<div class="window-title">.*?)(US NASDAQ & MEGA-CAP)', r'\1(A6) \2'),
    (r'(<div style="font-weight:700;font-size:14px;color:#fff;.*?)(Top 15 Alım Isı Haritası)', r'\1(A7) \2'),
    (r'(<div style="font-weight:700;font-size:14px;color:#fff;.*?)(Top 5 Alım Fırsatı)', r'\1(A7) \2')
]

for pat, repl in replacements:
    text, count = re.subn(pat, repl, text, flags=re.IGNORECASE)
    print(f"Replaced {count} occurrences for pattern: {pat}")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
