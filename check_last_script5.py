import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('ws.onclose = () => {')
start = idx - 500
sys.stdout.buffer.write(text[start:idx+500].encode('utf-8'))
