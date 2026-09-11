with open('templates/cand_merged.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Has market-window-crypto:", 'market-window-crypto' in text)
