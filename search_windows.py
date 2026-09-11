with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'Otonom Ö' in line or 'Koruma Kalkan' in line or 'Sentez' in line or 'Eğilim' in line:
        print(f"{i+1}: {line.strip()}")
