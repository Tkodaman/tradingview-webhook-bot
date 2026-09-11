with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i in range(1450, 1470):
    if i < len(lines):
        print(f"Line {i+1}: {lines[i].encode('ascii', 'ignore').decode()}")
