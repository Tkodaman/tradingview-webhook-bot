import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('seçildi. Hızlı emir penceresi')
start = max(0, idx - 10)
sys.stdout.buffer.write(repr(text[start:start+100]).encode('utf-8'))
