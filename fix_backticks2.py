with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == '}`;':
        continue
    new_lines.append(line)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Removed all exact }`; lines!")
