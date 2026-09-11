with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'const wsUrl' in line or 'function init' in line or 'document.addEventListener' in line:
        print(f"Line {i}: {line.strip()}")
