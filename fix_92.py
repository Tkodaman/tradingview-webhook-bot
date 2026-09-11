with open('templates/cand_92fbb.html', 'rb') as f:
    raw_data = f.read()
# Decode with 'cp1254' because it got mangled by PowerShell output which defaults to cp1254 in Turkish locale sometimes
decoded_text = raw_data.decode('cp1254', errors='ignore')
# Re-encode to pure utf-8
with open('templates/cand_92fbb_utf8.html', 'w', encoding='utf-8') as f:
    f.write(decoded_text)
print("Decoded cand_92fbb.html")
