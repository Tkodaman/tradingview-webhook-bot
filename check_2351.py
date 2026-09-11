with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
print(lines[2351].strip().encode('utf-8'))
