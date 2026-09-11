import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('function renderMarketGroup')
if idx1 != -1:
    idx2 = text.find('}', text.find('});', idx1)+3) + 1
    print(text[idx1:idx2])
