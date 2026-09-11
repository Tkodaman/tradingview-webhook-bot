with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

if 'NET KASA' in js:
    print("NET KASA found in JS!")
else:
    print("Not found in JS.")
