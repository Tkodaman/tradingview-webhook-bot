with open(r'templates\cand_22e24.html_clean.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '</head>' in line:
        print(f"Line {i+1}: {line.strip()}")
        print("Previous 5 lines:")
        for j in range(max(0, i-5), i):
            print(lines[j].strip())
