with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
for i in range(1485, 1495):
    if i < len(lines):
        print(f"Line {i}: {lines[i].strip().encode('utf-8')}")
