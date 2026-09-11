import sys
import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = [m.start() for m in re.finditer(r'<EPHEMERAL_MESSAGE>', text)]
print("Total occurrences:", len(matches))

for idx in matches:
    print(f"\n--- At index {idx} ---")
    sys.stdout.buffer.write(text[max(0, idx-50):idx+50].encode('utf-8'))

