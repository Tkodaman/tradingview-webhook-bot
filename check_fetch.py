with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i in range(180, 210):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}")
