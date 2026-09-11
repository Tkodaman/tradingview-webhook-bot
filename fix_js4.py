with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "if (balEl && data.account_balance !== undefined) {" in line:
        skip = True
        new_lines.append("                if (balEl && data.account_balance !== undefined) {\n")
        new_lines.append("                    lastAlpacaBalance = parseFloat(data.account_balance);\n")
        new_lines.append("                    balEl.innerText = $;\n")
        new_lines.append("                    const ce = document.getElementById('chartLatestEquity');\n")
        new_lines.append("                    if (ce) ce.innerText = $;\n")
        new_lines.append("                }\n")
    elif skip:
        if "if (freeCashEl && data.available_cash !== undefined) {" in line:
            skip = False
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Replaced syntax block successfully!")
