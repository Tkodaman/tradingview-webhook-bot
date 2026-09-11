with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.rfind('<script>')
print(text[idx:])
