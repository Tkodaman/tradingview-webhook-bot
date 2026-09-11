with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
print(repr(lines[196]))
