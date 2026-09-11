with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Aktif A')
import re
print(re.sub(r'[^\x00-\x7F]+', ' ', text[idx-200:idx+100]))
