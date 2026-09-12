with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# exact replacements
reps = {
    'TRADINGVIEW AI GATEWAY & 3-PİYASA CANLI KOKPİTİ': '(a1) TRADINGVIEW AI GATEWAY & 3-PİYASA CANLI KOKPİTİ',
    'Açık Pozisyonlar & Canlı Takip': '(a2) Açık Pozisyonlar & Canlı Takip',
    'Risk Yönetimi & Otonom Sentry': '(a3) Risk Yönetimi & Otonom Sentry',
    'Kripto Piyasası': '(a4) Kripto Piyasası',
    'TR BIST 100/30': '(a5) TR BIST 100/30',
    'US NASDAQ & MEGA-CAP': '(a6) US NASDAQ & MEGA-CAP',
    'Top 15 Alım Isı Haritası & Momentum (Canlı Fiyatlar)': '(a7) Top 15 Alım Isı Haritası & Momentum (Canlı Fiyatlar)'
}

for k, v in reps.items():
    text = text.replace(k, v)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done")
