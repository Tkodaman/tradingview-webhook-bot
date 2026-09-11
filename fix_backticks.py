import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the literal backticks that were mistakenly added
html = html.replace('String.fromCharCode(96) +', '')
html = html.replace('+ String.fromCharCode(96)', '')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
