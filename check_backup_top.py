with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines[:20]:
    print(repr(line))
