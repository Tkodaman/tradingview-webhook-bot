with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
lines[196] = "                }"
with open('pure_js_clean.js', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
