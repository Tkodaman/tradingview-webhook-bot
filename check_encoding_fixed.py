with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find("TRADINGVIEW")
print(text[idx-30:idx+80])
