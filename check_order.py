with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_aktif = text.find('Aktif Açık')
if idx_aktif == -1: idx_aktif = text.find('Aktif A')
idx_top15 = text.find('Top 15')

print(f"Aktif index: {idx_aktif}")
print(f"Top15 index: {idx_top15}")
