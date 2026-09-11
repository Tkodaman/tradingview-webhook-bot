import re
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find the exact string "Aktif Açık Pozisyonlar" or "Otonom"
idx1 = text.find('Aktif A')
if idx1 == -1:
    idx1 = text.find('Pozisyonlar &')

if idx1 != -1:
    print("Found active positions table at index", idx1)
    # print context
    print(text[idx1-200:idx1+200])
else:
    print("NOT FOUND IN WORKING BACKUP EITHER?!")
