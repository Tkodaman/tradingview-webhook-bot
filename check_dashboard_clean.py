with open('templates/dashboard_clean.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Size:", len(text))
print("Has Top 15:", "Top 15" in text)
print("Has Aktif:", "Aktif" in text)
print("Has CSS:", "<style>" in text)
print("Has duplicate Aktif:", text.count("Aktif A") > 1)
print("Has literal \\r:", "\\r" in text)
