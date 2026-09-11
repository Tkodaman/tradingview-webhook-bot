with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Literal \\t:", "\\t" in text)
print("Literal \\":", "\\"" in text)
