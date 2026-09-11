with open('templates/dashboard_clean.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class="wallet-bar"')
print(text[idx:idx+800])
