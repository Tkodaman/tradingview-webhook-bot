with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('KRPTO (Binance)')
print(text[idx-200:idx+2500].encode('ascii', 'ignore').decode('ascii'))
