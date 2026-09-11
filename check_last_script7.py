import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('ws.onclose = () => {')
start = idx
sys.stdout.buffer.write(text[start:start+500].encode('utf-8'))
