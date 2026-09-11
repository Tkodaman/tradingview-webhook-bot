import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('EPHEMERAL_MESSAGE')
print("Index after stripping:", idx)
