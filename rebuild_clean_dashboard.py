import re

with open('backup_html_structure.txt', 'r', encoding='utf-8') as f:
    html = f.read()

with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Swap the panels in HTML
# Panel 1: Aktif
p1_start = html.find('<div class="panel-container" style="display:flex; flex-direction:column; gap:20px;">')
if p1_start == -1:
    print("Could not find Aktif container.")
    exit(1)

main_grid_start = html.find('<div class="main-grid"')
main_grid_end = html.find('</div>\n    </div>\n    \n    <!-- RIGHT CONTENT (Live Log) -->')

main_grid_content = html[main_grid_start:main_grid_end]

top15_start = main_grid_content.find('<div class="panel-container">')
top15_end = main_grid_content.find('<div class="panel-container" style="display:flex; flex-direction:column; gap:20px;">')

aktif_start = top15_end
aktif_end = main_grid_content.rfind('</div>') + 6

if top15_start != -1 and aktif_start != -1:
    top15_html = main_grid_content[top15_start:top15_end]
    aktif_html = main_grid_content[aktif_start:aktif_end]
    
    # Swap them
    new_main_grid_content = main_grid_content[:top15_start] + aktif_html + "\n" + top15_html + "\n"
    
    html = html.replace(main_grid_content, new_main_grid_content)
    print("Swapped panels!")
else:
    print("Could not swap panels.")

# 2. Fix JS syntax errors in pure_js_clean.js
# - Fix ws.onopen
js = js.replace("showToast('WebSocket ile Canlı Veri Akışına Geçildi', 'info');\n\n            ws.onmessage", "showToast('WebSocket ile Canlı Veri Akışına Geçildi', 'info');\n            };\n\n            ws.onmessage")

# - Fix ws.onmessage
js = js.replace("console.error(\"WebSocket Message Error:\", e);\n                }\n\n            ws.onclose", "console.error(\"WebSocket Message Error:\", e);\n                }\n            };\n\n            ws.onclose")

# - Fix connectWebSocket missing }
js = js.replace("ws.onclose = () => {\n                console.log(\"WebSocket Bağlantısı Koptu, Yeniden Bağlanılıyor...\");\n                document.querySelector('.live-dot').style.backgroundColor = 'var(--down-color)';\n                setTimeout(connectWebSocket, 3000);\n        }", "ws.onclose = () => {\n                console.log(\"WebSocket Bağlantısı Koptu, Yeniden Bağlanılıyor...\");\n                document.querySelector('.live-dot').style.backgroundColor = 'var(--down-color)';\n                setTimeout(connectWebSocket, 3000);\n            };\n        }")

# - Fix card.onclick missing };
js = re.sub(r"(showToast\(\$\{item\.symbol\} se[çc]ildi\. Hızlı emir penceresi açıldı\., 'info'\);\r?\n\s*)\} else \{", r"\1};\n                } else {", js)

# 3. Rebuild dashboard.html
final_html = html + "\n<script>\n" + js + "\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Dashboard rebuilt successfully!")
