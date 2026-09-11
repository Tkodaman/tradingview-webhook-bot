with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('seçildi. Hızlı emir penceresi açıldı., \'info\');\n                } else {')
if idx != -1:
    print("Found it exactly!")
    text = text[:idx] + 'seçildi. Hızlı emir penceresi açıldı., \'info\');\n                    };\n                } else {' + text[idx + len('seçildi. Hızlı emir penceresi açıldı., \'info\');\n                } else {'):]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
else:
    print("Not found EXACTLY.")
