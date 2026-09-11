with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = "showToast(${item.symbol} seçildi. Hızlı emir penceresi açıldı., 'info');\n                } else {"
replacement = "showToast(${item.symbol} seçildi. Hızlı emir penceresi açıldı., 'info');\n                    };\n                } else {"

html = html.replace(target, replacement)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
