with open(r'templates\cand_22e24.html_clean.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '<div class=' in line or '<div id=' in line:
        print(f"FIRST HTML TAG FOUND AT Line {i+1}: {line.strip()[:100]}")
        print("Previous 10 lines:")
        for j in range(max(0, i-10), i):
            print(f"Line {j+1}: {lines[j].strip()}")
        break
