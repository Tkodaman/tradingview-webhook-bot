with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

reps = {
    'Aktif Açık Pozisyonlar & Kâr/Zarar Takibi': '(a2) Aktif Açık Pozisyonlar & Kâr/Zarar Takibi',
    'Algoritmik Risk & Bütçe Yönetimi': '(a3) Algoritmik Risk & Bütçe Yönetimi'
}

for k, v in reps.items():
    if k in text:
        text = text.replace(k, v)
        print("Replaced:", k)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
