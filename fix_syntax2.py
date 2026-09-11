import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the known syntax errors
text = text.replace("return idx === 0 ? 'Start' : İşlem #;", "return idx === 0 ? 'Start' : İşlem #;")

# Find any other "İşlem #" without backticks
matches = re.findall(r'[^]İşlem #', text)
print("Other İşlem #: ", matches)

# Find the other crash on line 5691
idx = text.find("borderColor = 'rgba")
print(text[idx-50:idx+50])
