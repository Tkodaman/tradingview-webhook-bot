with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Extract Top 15
matches_top15 = [m.start() for m in re.finditer(r'<div id="top5OpportunitiesWrap"', text)]
idx_top15 = matches_top15[0]
end_top15 = text.find('<!-- ACTIVE POSITIONS TABLE -->', idx_top15)

top15_html = text[idx_top15:end_top15]

# Extract Aktif
idx_aktif = end_top15
end_aktif = text.find('<!-- ========================================================================= -->', idx_aktif)

aktif_html = text[idx_aktif:end_aktif]

# Now swap them in the text
new_text = text[:idx_top15] + aktif_html + top15_html + text[end_aktif:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Swapped Aktif Açık Pozisyonlar and Top 15!")
