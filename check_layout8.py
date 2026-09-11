import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('END MAIN DASHBOARD GRID')
start = max(0, idx - 500)
end = min(len(text), idx + 20)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
