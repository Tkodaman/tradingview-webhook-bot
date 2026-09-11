with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("File size:", len(text))
print("Contains Top 15?", 'Top 15' in text)
print("Contains Aktif?", 'Aktif' in text)
print("Contains Komisyon?", 'Komisyon' in text)
print("Contains NET KASA?", 'NET KASA' in text)
