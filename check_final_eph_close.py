with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '</EPHEMERAL_MESSAGE>' in line:
        print(f"Line {i}: {line.strip().encode('utf-8')}")
