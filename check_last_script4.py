import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('ws.onopen')
sys.stdout.buffer.write(text[idx:idx+1000].encode('utf-8'))
