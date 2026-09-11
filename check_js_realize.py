with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

if 'REAL' in js:
    print("REAL found in JS!")
