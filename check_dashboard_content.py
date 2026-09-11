with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Contains table:", "<table" in text)
print("Contains main-grid:", "main-grid" in text)
print("Length:", len(text))
