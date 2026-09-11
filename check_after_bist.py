with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('bistCountdown')
if idx != -1:
    print(text[idx:idx+1500].encode('ascii', 'ignore').decode('ascii'))
