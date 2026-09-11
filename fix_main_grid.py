with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx_top15 = html.find('<div id="top5OpportunitiesWrap"')
if idx_top15 != -1:
    html = html[:idx_top15] + '\n    </div>\n    <!-- END MAIN DASHBOARD GRID -->\n' + html[idx_top15:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Closed main-grid successfully!")
