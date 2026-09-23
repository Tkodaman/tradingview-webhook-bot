with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# First, remove any existing (aX) tags so we don't duplicate
import re
text = re.sub(r'\(a\d+\)\s*', '', text)

reps = {
    'TRADINGVIEW AI GATEWAY & 3-PİYASA CANLI KOKPİTİ': '(a1) TRADINGVIEW AI GATEWAY & 3-PİYASA CANLI KOKPİTİ',
    'Aktif Açık Pozisyonlar & Kâr/Zarar Takibi': '(a2) Aktif Açık Pozisyonlar & Kâr/Zarar Takibi',
    'BINANCE Kripto Terminali': '(a3) BINANCE Kripto Terminali',
    'TR BIST Terminali': '(a4) TR BIST Terminali',
    'US NASDAQ Terminali': '(a5) US NASDAQ Terminali',
    'AutoTrader - Trade Breakdown & Execution Log': '(a6) AutoTrader - Trade Breakdown & Execution Log',
    'Otonom Öğrenilen Kurallar & Koruma Kalkanı': '(a7) Otonom Öğrenilen Kurallar & Koruma Kalkanı',
    'Günlük Piyasa Sentezi & Strateji Eğilimi': '(a8) Günlük Piyasa Sentezi & Strateji Eğilimi',
    'Top 15 Alım Isı Haritası & Momentum (Canlı Fiyatlar)': '(a9) Top 15 Alım Isı Haritası & Momentum (Canlı Fiyatlar)'
}

for k, v in reps.items():
    if k in text:
        text = text.replace(k, v)
        print("Replaced:", k)
    else:
        print("NOT FOUND:", k)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
