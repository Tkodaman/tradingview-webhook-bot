with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx1 = text.find('Seans Saati & Countdown')
idx2 = text.find('Risk Parametreleri')

if idx1 != -1 and idx2 != -1:
    print(text[idx1-100:idx2+100].encode('ascii', 'ignore').decode('ascii'))
