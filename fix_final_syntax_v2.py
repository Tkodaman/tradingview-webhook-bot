with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'balEl.innerText = $' not in line:
            lines[i] = "                    balEl.innerText = $;\n"
            print(f"Fixed line {i}")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
