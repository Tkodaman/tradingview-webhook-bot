with open('templates/dashboard_clean.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('wallet-bar')
print(text[idx-50:idx+500])
