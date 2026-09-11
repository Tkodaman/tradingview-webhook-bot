with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'balEl.innerText' in line:
        print(f"Line {i}: {line.strip()}")
