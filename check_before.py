with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('// --- NEW JS ---')
bottom_js = text[idx:]

idx2 = bottom_js.find('const res = await fetch')
print(bottom_js[idx2-200:idx2])
