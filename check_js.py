import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Extract script blocks and compile them to check for JS syntax errors using nodejs if available, or we can just print the exact function again.
match = re.search(r'function renderHeatmapBoxes[\s\S]*?\}', text)
if match:
    print(match.group(0))
