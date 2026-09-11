with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = """                    card.onclick = () => {
                        document.getElementById('newPosSymbol').value = item.symbol;
                        openNewPositionModal();
                        showToast(${item.symbol} seçildi. Hızlı emir penceresi açıldı., 'info');
                } else {"""

replacement = """                    card.onclick = () => {
                        document.getElementById('newPosSymbol').value = item.symbol;
                        openNewPositionModal();
                        showToast(${item.symbol} seçildi. Hızlı emir penceresi açıldı., 'info');
                    };
                } else {"""

if "seçildi. Hızlı emir penceresi" in html:
    print("Found exact string via partial match!")

html = html.replace("showToast(${item.symbol} seçildi. Hızlı emir penceresi açıldı., 'info');\n                } else {", "showToast(${item.symbol} seçildi. Hızlı emir penceresi açıldı., 'info');\n                    };\n                } else {")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
