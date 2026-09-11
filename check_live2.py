with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
idx = text.find('function fetchLiveMatrix')
if idx != -1:
    print(text[idx:idx+800])
