with open('templates/dashboard_headers_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="market-window([^"]*)"(.*?)(<div class="ticker-grid")', text, re.DOTALL)
for m in matches:
    cls = m.group(1).strip()
    header_content = m.group(2)
    
    notice_match = re.search(r'<div class="market-notice-banner[^"]*"([^>]*)>', header_content)
    notice_id = notice_match.group(1) if notice_match else "NO NOTICE"
    
    # get grid ID by checking the text just after ticker-grid
    grid_match = re.search(r'id="([^"]+)"', text[m.end():m.end()+50])
    grid_id = grid_match.group(1) if grid_match else "NO GRID"

    print(f"Window Class: {cls}")
    print(f"Notice attributes: {notice_id}")
    print(f"Grid ID: {grid_id}")
    print("-" * 60)
