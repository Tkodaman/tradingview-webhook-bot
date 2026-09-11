import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('Algoritmik Hata Pay')
if idx != -1:
    start_idx = text.rfind('<div class="panel"', 0, idx)
    
    # We need to find the matching closing </div> for this panel.
    div_count = 0
    in_div = False
    i = start_idx
    end_idx = -1
    
    while i < len(text):
        if text[i:i+4] == '<div':
            div_count += 1
            in_div = True
        elif text[i:i+6] == '</div>':
            div_count -= 1
            if in_div and div_count == 0:
                end_idx = i + 6
                break
        i += 1
        
    if start_idx != -1 and end_idx != -1:
        new_text = text[:start_idx] + text[end_idx:]
        with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Successfully removed the 'Algoritmik Hata Payı' panel.")
    else:
        print("Could not correctly parse div bounds.")
else:
    print("Could not find the text.")
