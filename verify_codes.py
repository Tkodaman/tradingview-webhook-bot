with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

for i in range(1, 8):
    code = f"(a{i})"
    if code in text:
        print(f"FOUND: {code}")
    else:
        print(f"MISSING: {code}")
