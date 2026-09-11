import sys

with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Aktif Açık Pozisyonlar & Kâr/Zarar Takibi')
start = max(0, idx - 500)
end = min(len(text), idx + 1000)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
