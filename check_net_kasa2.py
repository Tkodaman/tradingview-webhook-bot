import sys

with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('NET KASA')
start = max(0, idx - 400)
end = min(len(text), idx + 200)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
