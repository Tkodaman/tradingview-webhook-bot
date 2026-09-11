with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'<EPHEMERAL_MESSAGE>.*', '', text, flags=re.DOTALL)
text = re.sub(r'<truncated.*', '', text, flags=re.DOTALL)

with open('templates/cand_perfect_clean.html', 'w', encoding='utf-8') as f:
    f.write(text)
