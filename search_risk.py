with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'risk-btn' in line or 'Agresif' in line or 'Temkinli' in line:
        print(f"{i+1}: {line.strip()}")
