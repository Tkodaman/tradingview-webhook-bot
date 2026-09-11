with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Portföy Dağılımı')
if idx != -1:
    print(text[idx-200:idx+800].encode('ascii', 'ignore').decode('ascii'))
else:
    print("Not found")
