with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(60, 75):
    print(f"Line {i+1}: {lines[i].strip()}")
