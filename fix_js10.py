with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'balEl.innerText =' in line and 'parseFloat' in line and not '' in line:
        lines[i] = "                    balEl.innerText = ${parseFloat(data.account_balance).toFixed(2)};\n"
    if 'if (ce) ce.innerText =' in line and 'parseFloat' in line and not '' in line:
        lines[i] = "                    if (ce) ce.innerText = ${parseFloat(data.account_balance).toFixed(2)};\n"

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed using line-by-line replacement!")
