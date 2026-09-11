with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('MAIN DASHBOARD LAYOUT')
if idx != -1:
    end_idx = text.find('END MAIN DASHBOARD GRID', idx)
    content = text[idx:end_idx]
    
    # Let's find all first-level children of the flex container
    # Or just look for any flex rules or widths.
    matches = re.finditer(r'<div[^>]*style="[^"]*flex:[^"]*"', content)
    for m in matches:
        print(m.group(0))
        
    print("\nLooking for '350px' or '300px':")
    for m in re.finditer(r'<div[^>]*350px[^>]*>', content):
        print(m.group(0))
