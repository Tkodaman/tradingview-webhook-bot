import re
with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Has Aktif:", 'Aktif' in text)
print("Has tbody id='activePositionsBody':", 'activePositionsBody' in text)
print("Has function updatePositions:", 'updatePositions' in text)
