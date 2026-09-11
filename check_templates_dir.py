with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    if 'Jinja2Templates' in line:
        print(line.strip())
