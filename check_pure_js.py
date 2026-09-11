with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()
print("Length of pure_js_clean.js:", len(text))
idx = text.find('EPHEMERAL_MESSAGE')
print("Index of EPHEMERAL_MESSAGE in pure_js_clean.js:", idx)
