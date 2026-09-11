with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

text = text.replace('İşlem #', 'Islem #')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed Islem!")
