with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace literal \r\n with actual newline
text = text.replace('\\r\\n', '\n')
text = text.replace('\\n', '\n')
text = text.replace('\\r', '')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed literal escapes in dashboard.html. Size:", len(text))
