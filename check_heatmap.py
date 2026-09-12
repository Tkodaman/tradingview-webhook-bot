with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
# Find the line that has 'Top 15 Alım Isı Haritası'
for i, line in enumerate(text.split('\n')):
    if 'Top 15' in line or 'Isı Haritası' in line:
        print(f"Line {i+1}: {line.strip()}")
        # print 5 lines before and after
        for j in range(max(0, i-5), min(len(text.split('\n')), i+6)):
            print(f"  {j+1}: {text.split('\n')[j].strip()}")
