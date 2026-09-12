import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

output = []
for term in ['TRADINGVIEW AI', 'Açık Pozisyonlar', 'Risk Yönetimi', 'Kripto Piyasası', 'TR BIST', 'US NASDAQ', 'Top 15']:
    idx = text.find(term)
    if idx != -1:
        start = max(0, idx - 50)
        end = min(len(text), idx + 100)
        output.append(f"TERM: {term}")
        output.append(text[start:end])
        output.append("-" * 40)

with open('debug_titles.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
