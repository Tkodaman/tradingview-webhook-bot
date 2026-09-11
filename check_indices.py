with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

aktif_idx = text.find('Aktif Açık')
if aktif_idx == -1: aktif_idx = text.find('Aktif A')
top15_idx = text.find('Top 15')

print("Aktif index:", aktif_idx)
print("Top 15 index:", top15_idx)
