import re

with open('templates/cand_perfect.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Remove the whole block from "The following is an <EPHEMERAL_MESSAGE>" up to "</EPHEMERAL_MESSAGE>"
text = re.sub(r'The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'The above content does NOT show.*?those lines\.\n', '', text)
text = re.sub(r'"\}', '', text) # Any dangling trailing "} from the JSON line
text = text.replace('"}', '')
text = text.replace('{"step_index"', '')

with open('templates/cand_perfect2.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Removed all ephemeral blocks! Length:", len(text))
