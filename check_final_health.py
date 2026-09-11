with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Has CSS:", "<style>" in text)
print("Has Grid:", "main-grid" in text)
print("Has Top 15:", "Top 15" in text)
print("Has Aktif:", "Aktif A" in text)
print("First 15 lines:")
for line in text.split('\n')[:15]:
    print(repr(line))
