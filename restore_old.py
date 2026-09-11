import codecs

# Read UTF-16
with open(r'_archive\dashboard_old.html', 'r', encoding='utf-16') as f:
    text = f.read()

# The WebSocket and reset-account endpoints need to be fixed
text = text.replace("/api/account/reset", "/api/positions/reset-account")

# Write to UTF-8
with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Restored from _archive/dashboard_old.html to templates/dashboard.html in UTF-8!")
