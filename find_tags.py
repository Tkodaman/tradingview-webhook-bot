with open(r'templates\cand_22e24.html_clean.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '</script>' in line or '<body>' in line or '<div' in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
