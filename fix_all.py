with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Replace any literal backslash r backslash n strings with actual newline
text = text.replace('\\r\\n', '\n')
text = text.replace('\\n', '\n')
text = text.replace('\\r', '')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced all escaped newlines.")
