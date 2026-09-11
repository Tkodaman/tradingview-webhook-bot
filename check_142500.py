with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
print(text[142500:142650].encode('ascii', 'ignore').decode('ascii'))
