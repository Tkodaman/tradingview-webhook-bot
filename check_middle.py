with open(r'templates\cand_22e24.html_clean.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Line 200:", lines[200].strip())
print("Line 500:", lines[500].strip())
print("Line 1000:", lines[1000].strip())
print("Line 1500:", lines[1500].strip())
