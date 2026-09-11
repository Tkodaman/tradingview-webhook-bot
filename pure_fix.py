with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if 'return idx === 0' in lines[i] and 'Start' in lines[i]:
        lines[i] = "            return idx === 0 ? 'Start' : İşlem #;\n"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed line 1283!")
