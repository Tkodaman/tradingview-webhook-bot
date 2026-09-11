with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('market-window-crypto')
print(text[idx:idx+500])
