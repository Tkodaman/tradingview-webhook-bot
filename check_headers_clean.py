with open('templates/dashboard_clean.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="market-window([^"]*)"', text)
for m in matches:
    start_idx = m.start()
    end_idx = text.find('class="ticker-grid"', start_idx)
    content = text[start_idx:end_idx+60]
    
    grid_match = re.search(r'class="ticker-grid"\s+id="([^"]+)"', content)
    grid_id = grid_match.group(1) if grid_match else "NO GRID"
    
    print(f"Window Class: {m.group(1)}")
    print(f"Grid ID: {grid_id}")
    print("-" * 40)
