with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()
if 'flashGreen' in html and 'repeat(2, 1fr)' in html:
    print("Changes are present.")
else:
    print("Changes are missing.")
