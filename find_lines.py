with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

search_terms = ['TRADINGVIEW AI', 'Açık Pozisyonlar', 'Risk Yönetimi', 'Kripto Piyasası', 'TR BIST', 'US NASDAQ', 'Top 15']

for i, line in enumerate(lines):
    for term in search_terms:
        if term in line:
            print(f"Line {i+1}: {line.strip()[:150]}")
