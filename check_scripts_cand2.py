import re

with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

scripts = text.split('<script')
print(f"Number of <script tags: {len(scripts)-1}")

for i, s in enumerate(scripts[1:5]):
    # Find closing tag
    idx_close = s.find('>')
    idx_end = s.find('</script>')
    content = s[idx_close+1:idx_end].strip()
    print(f"Script {i}: length {len(content)}, startswith: {content[:50]}")
