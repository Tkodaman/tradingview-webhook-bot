with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Portf')
if idx != -1:
    print(text[idx-50:idx+200].encode('ascii', 'ignore').decode('ascii'))
else:
    print("Not found")
