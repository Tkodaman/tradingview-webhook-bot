import re

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Replace all ephemeral messages
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'<truncated.*?bytes>', '', text, flags=re.DOTALL)
text = re.sub(r'NOTE: The output was truncated.*?information you need.', '', text, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Removed all!")
