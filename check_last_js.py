with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i, line in enumerate(lines[-100:]):
    print(f"Line {len(lines) - 100 + i + 1}: {line}")
