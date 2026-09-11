with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Fix the IDs in Javascript
text = text.replace("renderMarketGroup('gridCrypto'", "renderMarketGroup('windowCrypto'")
text = text.replace("renderMarketGroup('gridBist'", "renderMarketGroup('windowBist'")
text = text.replace("renderMarketGroup('gridNasdaq'", "renderMarketGroup('windowNasdaq'")

# Fix syntax 1
text = text.replace("return idx === 0 ? 'Start' : İşlem #;", "return idx === 0 ? 'Start' : İşlem #;")

# Find where the truncation starts and chop it!
import re
idx_trunc = text.find('borderColor = \'rgba\n<truncated')
if idx_trunc != -1:
    text = text[:idx_trunc] + "borderColor = 'rgba(234,179,8,0.18)';\n}\n}\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Absolute fix!")
