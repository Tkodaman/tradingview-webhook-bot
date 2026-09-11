with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Portfy')
if idx != -1:
    print(text[idx-50:idx+2500].encode('ascii', 'ignore').decode('ascii'))
