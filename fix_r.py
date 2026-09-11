with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Replace the literal string "\r" with nothing
text = text.replace('\\r', '')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed literal r characters!")
