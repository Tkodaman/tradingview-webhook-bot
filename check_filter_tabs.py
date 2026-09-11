import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find('class="filter-tabs"')
if idx != -1:
    print(re.sub(r'[^\x00-\x7F]+', ' ', text[max(0, idx-500):idx+200]))
