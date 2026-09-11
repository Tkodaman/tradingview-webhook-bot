with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Find the panel container that has "15 Momentum"
idx = text.find('15 Momentum')
if idx != -1:
    start_idx = text.rfind('<div class="panel-container"', 0, idx)
    # find the matching closing div. It has some nested divs, so we need to count
    div_count = 0
    end_idx = start_idx
    while end_idx < len(text):
        if text[end_idx:end_idx+4] == '<div':
            div_count += 1
        elif text[end_idx:end_idx+5] == '</div':
            div_count -= 1
            if div_count == 0:
                end_idx += 6
                break
        end_idx += 1
        
    top15_html = text[start_idx:end_idx]
    with open('top15.html', 'w', encoding='utf-8') as f:
        f.write(top15_html)
    print("Extracted top15.html")
else:
    print("Could not find 15 Momentum")
