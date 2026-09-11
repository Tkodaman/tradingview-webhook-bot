with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix ws.onopen
html = html.replace("showToast('WebSocket ile Canlı Veri Akışına Geçildi', 'info');\n\n            ws.onmessage", "showToast('WebSocket ile Canlı Veri Akışına Geçildi', 'info');\n            };\n\n            ws.onmessage")

# Fix ws.onmessage
html = html.replace("console.error(\"WebSocket Message Error:\", e);\n                }\n\n            ws.onclose", "console.error(\"WebSocket Message Error:\", e);\n                }\n            };\n\n            ws.onclose")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
