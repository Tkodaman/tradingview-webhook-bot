with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("First 200 chars:")
print(repr(text[:200]))
