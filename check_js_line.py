with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(lines[1462].encode('ascii', 'ignore').decode().strip())
