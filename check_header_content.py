with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="market-window([^"]*)"(.*?)(<div class="ticker-grid" id="[^"]+">)', text, re.DOTALL)
for m in matches:
    cls = m.group(1).strip()
    grid_line = m.group(3)
    header_content = m.group(2)
    
    print(f"Window Class: {cls}")
    print(f"Grid line: {grid_line}")
    # Let's extract the header title text manually
    title_idx = header_content.find('<div class="window-header">')
    if title_idx != -1:
        print(header_content[title_idx:title_idx+200].encode('ascii', 'ignore').decode())
    print("-" * 60)
