with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
issues = re.findall(r'[^\x00-\x7F]', text)
# check if any literal '' is in the text
if '\ufffd' in text:
    print("Found literal replacement char:", text.count('\ufffd'))
