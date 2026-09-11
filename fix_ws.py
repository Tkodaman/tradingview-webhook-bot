with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('/ws/live', '/live')

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
