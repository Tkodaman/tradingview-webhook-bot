with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('grid-template-columns: 1fr 1fr 1fr')
print(text[max(0, idx-100):idx+200])
