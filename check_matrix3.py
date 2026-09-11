with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('/api/market/live-matrix')
if idx != -1:
    start = max(0, idx - 200)
    end = min(len(text), idx + 800)
    lines = text[start:end].split('\n')
    for line in lines:
        print(line.encode('ascii', 'ignore').decode())
