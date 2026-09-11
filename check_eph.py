with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

if '<EPHEMERAL_MESSAGE>' in html:
    print("YES! EPHEMERAL IS IN THE FILE!")
else:
    print("NO, IT'S NOT IN THE FILE.")
