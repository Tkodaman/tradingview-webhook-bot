import re
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Has market-window-crypto:", 'market-window-crypto' in text)
print("Has market-window-bist:", 'market-window-bist' in text)
