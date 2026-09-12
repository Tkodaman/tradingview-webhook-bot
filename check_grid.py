with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
for i, line in enumerate(text.split('\n')):
    if 'grid-template-columns' in line and ('heatmap' in text[max(0, i*50-500):i*50+500] or 'market-group' in text[max(0, i*50-500):i*50+500]):
        print(f"Line {i+1}: {line}")
