with open('templates/cand_perfect.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re

# Some chunks of the transcript might have " at the end or "{"step_index":7"
# Let's search for "{"step_index"
idx = text.find('{"step_index')
print("Found step index:", idx)
idx2 = text.find('EPHEMERAL_MESSAGE')
print("Found ephemeral:", idx2)
