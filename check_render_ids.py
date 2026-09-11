with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'renderMarketGroup\((.*?)\)', text)
print("render calls:", matches)

print("ID gridCrypto:", text.find('id="gridCrypto"'))
print("ID windowCrypto:", text.find('id="windowCrypto"'))
print("ID windowBist:", text.find('id="windowBist"'))
print("ID windowNasdaq:", text.find('id="windowNasdaq"'))

# look for the actual divs in the html!
print(text.find("KRİPTO VARLIKLARI"))
