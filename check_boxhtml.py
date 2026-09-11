with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'const boxHtml =' in line:
        start = max(0, i)
        end = min(len(lines), i+15)
        print(f"--- boxHtml ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
