import re

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# The system prompt includes "The following is an <EPHEMERAL_MESSAGE> not actually sent by the user... </EPHEMERAL_MESSAGE>"
# Let's remove any such block.

text = re.sub(r'The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Cleaned dashboard.html. Size:", len(text))
