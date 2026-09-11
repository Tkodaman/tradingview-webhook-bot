with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to find the <div class="panel-container"> that contains "Top 15"
idx_top15 = text.find('Top 15')
start_top15 = text.rfind('<div class="panel-container"', 0, idx_top15)

# We need to find the <div class="panel-container"> that contains "Aktif"
idx_aktif = text.find('Aktif A', start_top15 + 10)
if idx_aktif == -1: idx_aktif = text.find('Aktif Açık', start_top15 + 10)

# The end of top15 container is the start of aktif container
end_top15 = text.rfind('<div class="panel-container"', start_top15 + 1, idx_aktif)
if end_top15 == -1:
    end_top15 = text.find('<div class="panel-container"', start_top15 + 10)

start_aktif = end_top15

# The end of aktif container is just before <!-- RIGHT CONTENT (Live Log) -->
end_aktif = text.find('<!-- RIGHT CONTENT (Live Log) -->', start_aktif)
# But we must leave the closing divs of main-grid intact.
# The main-grid closes just before RIGHT CONTENT.
end_aktif = text.rfind('</div>\n    </div>', start_aktif, end_aktif)

print(f"Top15: {start_top15} to {end_top15}")
print(f"Aktif: {start_aktif} to {end_aktif}")

if start_top15 != -1 and end_top15 != -1 and start_aktif != -1 and end_aktif != -1:
    top15_html = text[start_top15:end_top15]
    aktif_html = text[start_aktif:end_aktif]
    
    new_text = text[:start_top15] + aktif_html + "\n" + top15_html + "\n" + text[end_aktif:]
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Successfully swapped panels!")
