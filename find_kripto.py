with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('Kripto Piyasas')
print(text[idx-200:idx+300].encode('ascii', 'ignore').decode('ascii'))
