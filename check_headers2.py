with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="market-window([^"]*)"', text)
for m in matches:
    start_idx = m.start()
    end_idx = text.find('class="ticker-grid"', start_idx)
    # Give some buffer after ticker-grid to get the ID
    content = text[start_idx:end_idx+60]
    
    # Extract Title
    title_match = re.search(r'<div class="window-header-title">(.*?)</div>', content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "NO TITLE"
    
    # Extract Grid ID
    grid_match = re.search(r'class="ticker-grid"\s+id="([^"]+)"', content)
    grid_id = grid_match.group(1) if grid_match else "NO GRID"
    
    print(f"Window Class: {m.group(1)}")
    print(f"Grid ID: {grid_id}")
    print(f"Title: {re.sub(r'<[^>]+>', '', title).strip().encode('ascii', 'ignore').decode()}")
    print("-" * 40)
