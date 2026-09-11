with open('templates/cand_92fbb.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Has websocket logic:", 'wsUrl' in text)
print("Has Kripto:", 'market-window-crypto' in text)
print("Has top 10 momentum:", 'top10CryptoBody' in text)
print("Line count:", text.count('\n'))
