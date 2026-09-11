with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'balEl.innerText =' in line:
        print(f"Line {i+1}: {line.strip()}")
