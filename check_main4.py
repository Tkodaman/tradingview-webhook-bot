with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'TemplateResponse' in line:
        for j in range(i, min(len(lines), i+5)):
            print(f"Line {j+1}: {lines[j].strip()}")
        break
