with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2105, 2115):
    if i < len(lines):
        print(f"Line {i+1}: {lines[i].strip()}")
