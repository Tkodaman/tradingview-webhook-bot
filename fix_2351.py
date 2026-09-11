with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "return idx === 0 ? 'Start' :" in lines[i] and 'lem #' in lines[i]:
        lines[i] = "                return idx === 0 ? 'Start' : 'Islem #' + idx;\n"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed syntax error!")
