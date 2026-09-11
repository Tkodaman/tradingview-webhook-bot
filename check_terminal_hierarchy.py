with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('Kripto Terminali')
start = text.rfind('<div', 0, idx)
parent_start = text.rfind('<div', 0, start)
grand_start = text.rfind('<div', 0, parent_start)
great_grand = text.rfind('<div', 0, grand_start)
great_great = text.rfind('<div', 0, great_grand)

print(text[great_great:idx+150].encode('ascii', 'ignore').decode())
