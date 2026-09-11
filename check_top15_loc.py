import sys

with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Top 15')
start = max(0, idx - 500)
end = min(len(text), idx + 500)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
