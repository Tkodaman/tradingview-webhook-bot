with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

lines = js.split('\n')
for i in range(520, 540):
    if i < len(lines):
        print(f"Line {i+1}: {lines[i]}")
