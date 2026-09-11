import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('console.error("WebSocket Message Error:", e);')
start = idx - 100
sys.stdout.buffer.write(text[start:start+300].encode('utf-8'))
