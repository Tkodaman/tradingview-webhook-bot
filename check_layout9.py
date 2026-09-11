import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('<body>')
start = idx
end = min(len(text), idx + 2000)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
