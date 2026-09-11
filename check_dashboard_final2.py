with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Length:", len(text))
print("Contains Top 15:", "Top 15" in text)
print("Contains \\r literal:", "\\r" in text)
