with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('🔥 Top 15')
start = max(0, idx - 400)
end = min(len(text), idx + 20)

import sys
sys.stdout.buffer.write(text[start:end].encode('utf-8'))
