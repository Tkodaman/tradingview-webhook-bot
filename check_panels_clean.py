import re

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Find all panel-containers
matches = re.finditer(r'<div class="panel-container"', text)
starts = [m.start() for m in matches]
starts.append(len(text))

print(f"Total panel containers: {len(starts)-1}")
for i in range(len(starts)-1):
    snippet = text[starts[i]:starts[i]+300]
    clean = re.sub(r'[^\x00-\x7F]+', ' ', snippet).replace('\n', ' ')
    
    # Try to find a header
    h_match = re.search(r'panel-header-title[^>]*>(.*?)</div>', snippet, re.DOTALL)
    if h_match:
        h_text = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
        h_text = re.sub(r'[^\x00-\x7F]+', ' ', h_text).strip()
        print(f"Panel {i+1}: {h_text}")
    else:
        print(f"Panel {i+1}: No title found, start={starts[i]}")

