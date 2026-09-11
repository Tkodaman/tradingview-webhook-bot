with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i, line in enumerate(lines):
    if '' in line and (';' in line or '{' in line or ')' in line):
        print(f"Line {i+1}: {line}")
