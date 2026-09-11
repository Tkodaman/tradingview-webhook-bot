with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace literal \r and \n
text = text.replace('\\r', '')
text = text.replace('\\n', '\n')
text = text.replace('\\t', '\t')
# What if there are escaped quotes like \"?
text = text.replace('\\"', '"')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed literal escapes in dashboard.html")
