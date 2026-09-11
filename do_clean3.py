import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r"return idx === 0 \? 'Start' : [^;]+;", "return idx === 0 ? 'Start' : İşlem #;", text)

idx_eph = text.find('<EPHEMERAL_MESSAGE>')
if idx_eph != -1:
    text = text[:idx_eph]
    # Check if there is an unclosed string "rgba" at the end
    idx_rgba = text.rfind("borderColor = 'rgba")
    if text.endswith("borderColor = 'rgba"):
        text = text.replace("borderColor = 'rgba", "borderColor = 'rgba(234,179,8,0.18)';\n")

# Need to make sure the script tag is closed
if text.count('<script>') > text.count('</script>'):
    # let's balance the brackets
    opens = text.count('{')
    closes = text.count('}')
    diff = opens - closes
    if diff > 0:
        text += '}\n' * diff
    text += '</script>\n</body>\n</html>'

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("CLEANSED HTML 3!")
