with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("checkLiveStatus();", "// checkLiveStatus();")

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Commented out checkLiveStatus()")
