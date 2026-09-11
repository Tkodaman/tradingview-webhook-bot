import re

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Remove Ephemeral Messages block completely
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'<truncated.*?bytes>', '', text, flags=re.DOTALL)
text = re.sub(r'NOTE: The output was truncated.*?information you need.', '', text, flags=re.DOTALL)

# Fix the known Javascript issues
text = text.replace("return idx === 0 ? 'Start' : İşlem #;", "return idx === 0 ? 'Start' : İşlem #;")

# For the line: else if (item.icon === '🟡') borderColor = 'rgba
# It was truncated. Let's find it and close it properly.
idx = text.find("borderColor = 'rgba\n")
if idx != -1:
    text = text.replace("borderColor = 'rgba\n", "borderColor = 'rgba(234,179,8,0.18)';\n")

# Remove any empty lines that might have been left over
text = re.sub(r'\n\s*\n', '\n', text)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("CLEANSED HTML!")
