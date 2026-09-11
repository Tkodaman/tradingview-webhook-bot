with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Top 15 count:", text.count("Top 15 Al"))
print("Aktif count:", text.count("Aktif A"))
