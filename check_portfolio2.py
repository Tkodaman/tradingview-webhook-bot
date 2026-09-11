with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Portf')
if idx != -1:
    print(text[idx-200:idx+2000].encode('ascii', 'ignore').decode('ascii'))
else:
    print("Not found")
