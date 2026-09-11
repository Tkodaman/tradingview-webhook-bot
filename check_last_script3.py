import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.rfind('<script>')
start = idx + 20000
sys.stdout.buffer.write(text[start:start+1000].encode('utf-8'))
