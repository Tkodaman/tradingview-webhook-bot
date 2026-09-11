with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'<div class="market-window([^"]*)"(.*?)(<div class="ticker-grid")', text, re.DOTALL)
for m in matches:
    cls = m.group(1).strip()
    header_content = m.group(2)
    
    notice_match = re.search(r'<div class="market-notice-banner[^"]*" id="([^"]+)">', header_content)
    notice_id = notice_match.group(1) if notice_match else "NO NOTICE"
    
    print(f"Window Class: {cls}")
    print(f"Notice ID: {notice_id}")
    print("-" * 60)
