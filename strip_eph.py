import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Completely strip any ephemeral messages. They shouldn't be in the code!
# We must use regex to catch variations of it.
pattern = r"The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>"
html = re.sub(pattern, '', html, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Stripped ephemeral!")
