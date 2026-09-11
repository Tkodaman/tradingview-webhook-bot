with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

if 'risk-mode' in text:
    print("YES risk-mode is present!")
else:
    print("NO risk-mode is not present!")
