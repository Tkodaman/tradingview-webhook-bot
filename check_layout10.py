import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('<!-- 8. Komisyon -->')
start = max(0, idx - 1000)
end = min(len(text), idx + 200)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
