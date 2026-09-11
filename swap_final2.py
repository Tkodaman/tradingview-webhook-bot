with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Find Top 15 container
start1 = text.rfind('<div class="panel-container"', 0, text.find('Top 15'))
end1 = text.find('<div class="panel-container"', start1 + 10)

# Find Aktif container
start2 = end1
end2 = text.find('<!-- RIGHT CONTENT', start2)

if start1 != -1 and end1 != -1 and start2 != -1 and end2 != -1:
    top15 = text[start1:end1]
    # To correctly extract aktif, we must find its closing div before "RIGHT CONTENT"
    aktif = text[start2:text.rfind('</div>', start2, end2) + 6]
    
    # Actually, let's just find "Aktif" string
    aktif_idx = text.find('Aktif Açık')
    if aktif_idx == -1: aktif_idx = text.find('Aktif A')
    
    if start1 < aktif_idx:
        # Swap
        new_text = text[:start1] + text[start2:end2] + "\n" + text[start1:end1] + "\n" + text[end2:]
        with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Swapped using slicing!")
