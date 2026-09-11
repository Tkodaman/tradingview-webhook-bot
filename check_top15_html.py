with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx_top15 = text.find('Top 15')
if idx_top15 != -1:
    clean = re.sub(r'[^\x00-\x7F]+', ' ', text[idx_top15-200:idx_top15+50])
    print(clean)
