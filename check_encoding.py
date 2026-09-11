with open('dashboard_rebuilt_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Title:", text[:100])
print("Aktif Pozisyonlar:", text.find("Aktif Pozisyonlar"))
print("TRADINGVIEW", text.find("TRADINGVIEW"))
