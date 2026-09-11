with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'parseFloat(data.account_balance)' in line:
        for j in range(i-2, i+5):
            print(f"Line {j+1}: {repr(lines[j])}")
        break
