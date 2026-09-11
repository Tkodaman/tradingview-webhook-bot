with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
    
import re
idx = text.find('// --- NEW JS ---')
bottom_js = text[idx:]
lines = bottom_js.split('\n')
for line in lines:
    if line.startswith('const ') or line.startswith('let ') or line.startswith('var '):
        print("Top level:", line)
