with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('checkLiveStatus();', '// checkLiveStatus();')

with open('pure_js_clean.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Commented out checkLiveStatus();")
