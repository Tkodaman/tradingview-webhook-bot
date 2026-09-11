with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('The following is an <EPHEMERAL_MESSAGE>')
print("Found at:", idx)

# Remove all occurrences of the garbage!
# We want to remove from 'The following is an <EPHEMERAL_MESSAGE>' to the next '</EPHEMERAL_MESSAGE>' AND any following whitespace!
import re
new_text = re.sub(r"The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>\s*", "", text, flags=re.DOTALL)
new_text = re.sub(r"<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>\s*", "", new_text, flags=re.DOTALL)

with open('templates/dashboard_clean.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Created dashboard_clean.html")
