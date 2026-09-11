with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('FUTURE ADVANCING ENGINE')
if idx != -1:
    print(text[idx-200:idx+200])
