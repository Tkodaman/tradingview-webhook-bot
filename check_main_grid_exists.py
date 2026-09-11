import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('<div class="main-grid">')
if idx == -1:
    print("NO MAIN-GRID FOUND!!!")
else:
    print("MAIN GRID FOUND AT:", idx)
