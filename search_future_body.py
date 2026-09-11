with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'id="futureStreamContainer"' in line or 'class="future-body"' in line:
        start = max(0, i-5)
        end = min(len(lines), i+15)
        print(f"--- line {i+1} ---")
        for j in range(start, end):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
