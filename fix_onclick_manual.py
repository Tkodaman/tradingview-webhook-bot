with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "showToast(`${item.symbol} seçildi. Hızlı emir penceresi açıldı.`, 'info');" in line:
        new_lines.append(line)
        # Check if the next line has '} else {'
        if i + 1 < len(lines) and '} else {' in lines[i+1]:
            new_lines.append("                    };\n")
    else:
        new_lines.append(line)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Inserted }; manually.")
