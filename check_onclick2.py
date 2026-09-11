import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('seçildi. Hızlı emir penceresi')
start = max(0, idx - 100)
sys.stdout.buffer.write(text[start:start+200].encode('utf-8'))
