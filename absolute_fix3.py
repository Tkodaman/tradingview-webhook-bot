with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Fix the IDs in Javascript
for i in range(len(lines)):
    lines[i] = lines[i].replace("renderMarketGroup('gridCrypto'", "renderMarketGroup('windowCrypto'")
    lines[i] = lines[i].replace("renderMarketGroup('gridBist'", "renderMarketGroup('windowBist'")
    lines[i] = lines[i].replace("renderMarketGroup('gridNasdaq'", "renderMarketGroup('windowNasdaq'")

# Fix syntax 1 exactly at line 2351
for i in range(len(lines)):
    if 'return idx === 0' in lines[i] and 'Start' in lines[i]:
        lines[i] = "            return idx === 0 ? 'Start' : İşlem #;\n"

# Join lines back
text = "".join(lines)

# Find where the truncation starts and chop it!
idx_trunc = text.find("borderColor = 'rgba\n<truncated")
if idx_trunc != -1:
    text = text[:idx_trunc] + "borderColor = 'rgba(234,179,8,0.18)';\n}\n}\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Absolute index fix!")
