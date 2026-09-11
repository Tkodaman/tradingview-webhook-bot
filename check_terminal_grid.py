with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('Kripto Terminali')
start = text.rfind('<div class="', 0, idx)
parent_start = text.rfind('<div class="', 0, start)
print("Parent context:", text[parent_start:start])
print("Grid context:", text[start:idx+50])
