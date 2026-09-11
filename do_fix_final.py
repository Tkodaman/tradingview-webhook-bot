with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# 1. Fix the IDs in Javascript
text = text.replace("renderMarketGroup('gridCrypto'", "renderMarketGroup('windowCrypto'")
text = text.replace("renderMarketGroup('gridBist'", "renderMarketGroup('windowBist'")
text = text.replace("renderMarketGroup('gridNasdaq'", "renderMarketGroup('windowNasdaq'")

# 2. Fix the syntax error İşlem #
import re
text = re.sub(r"return idx === 0 \? 'Start' : [^;]+;", "return idx === 0 ? 'Start' : İşlem #;", text)

# 3. Fix the truncated rgba string
text = re.sub(r"borderColor = 'rgba\n<truncated.*?<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>", "borderColor = 'rgba(234,179,8,0.18)';\n}\n}\n", text, flags=re.DOTALL)

# 4. Remove ALL OTHER <EPHEMERAL_MESSAGE> blocks entirely!
# The ephemeral message starts with <EPHEMERAL_MESSAGE> and ends with </EPHEMERAL_MESSAGE>.
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>\n?', '', text, flags=re.DOTALL)
text = re.sub(r'<truncated.*?bytes>\n?', '', text, flags=re.DOTALL)
text = re.sub(r'NOTE: The output was truncated.*?information you need\.\n?', '', text, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("ID and Syntax fixed and clean!")
