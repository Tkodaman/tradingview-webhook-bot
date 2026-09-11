with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('async function fetchLiveMatrix')
if idx != -1:
    print(text[idx:idx+1500].encode('ascii', 'ignore').decode('ascii'))
