with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="gridCrypto"')
if idx != -1:
    print(text[idx-50:idx+250].encode('ascii', 'ignore').decode('ascii'))
else:
    print("Not found")
