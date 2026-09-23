with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find the start of Top 15 div
idx_top15 = text.find('Top 15 Al')
if idx_top15 != -1:
    top15_start = text.rfind('<div style="background:linear-gradient', 0, idx_top15)
    if top15_start != -1:
        text = text[:top15_start] + text[top15_start:].replace('<div style="background:linear-gradient', '<div style="order:2; background:linear-gradient', 1)

# Find the start of Aktif Açık div
idx_aktif = text.find('Aktif A')
if idx_aktif != -1:
    aktif_start = text.rfind('<div class="panel-container"', 0, idx_aktif)
    if aktif_start != -1:
        text = text[:aktif_start] + text[aktif_start:].replace('<div class="panel-container"', '<div class="panel-container" style="order:1;"', 1)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added CSS flex order successfully!")
