with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[1950:2050]):
    print(f"{1950+i}: {line.rstrip()}")
