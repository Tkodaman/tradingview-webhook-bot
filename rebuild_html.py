import re

with open('backup_html_structure.txt', 'r', encoding='utf-8') as f:
    html = f.read()

# Let's see if backup_html_structure.txt has Aktif Açık Pozisyonlar and Top 15 Momentum
idx1 = html.find('Top 15 Momentum')
idx2 = html.find('Aktif Açık Pozisyonlar')
print("Top 15 Momentum at:", idx1)
print("Aktif Açık Pozisyonlar at:", idx2)

