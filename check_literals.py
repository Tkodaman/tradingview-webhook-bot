with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Contains literal backslash r:", "\\r" in text)
print("Contains literal backslash n:", "\\n" in text)
