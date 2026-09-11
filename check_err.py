with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i in range(1378, 1388):
    if i < len(lines):
        print(f"Line {i+1}: {lines[i]}")
