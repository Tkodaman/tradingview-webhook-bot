with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
print("Contains \\n as literal:", '\\n' in text)
