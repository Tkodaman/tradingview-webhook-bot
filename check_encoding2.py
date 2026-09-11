with open('dashboard_rebuilt_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find("TRADINGVIEW")
print(text[idx-50:idx+150])
