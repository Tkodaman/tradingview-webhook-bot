with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
    
print("Has windowCrypto HTML?:", 'windowCrypto' in text)
print("Has KRIPTO VARLIKLARI HTML?:", "KRIPTO" in text.upper())
print("File size:", len(text))
