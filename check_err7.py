with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1458, 1466):
    print(f"Line {i+1}: {lines[i].strip()}")
