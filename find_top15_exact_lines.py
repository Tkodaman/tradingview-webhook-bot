with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Top 15" in line:
        print(f"Found 'Top 15' at line {i}")
        for j in range(max(0, i-5), min(len(lines), i+15)):
            try:
                print(f"{j}: {lines[j].strip()}")
            except UnicodeEncodeError:
                pass
