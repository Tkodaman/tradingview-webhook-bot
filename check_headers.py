import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find each market-window and print its header title and the grid ID inside it
matches = re.finditer(r'<div class="market-window([^"]*)".*?(<div class="window-header-title">.*?</div>).*?id="(grid[A-Za-z]+)"', text, re.DOTALL)
for m in matches:
    cls = m.group(1).strip()
    title_html = m.group(2)
    grid_id = m.group(3)
    
    # Strip HTML tags from title for clean output
    title_text = re.sub(r'<[^>]+>', '', title_html).strip()
    # Also clean up unicode
    title_text = re.sub(r'[^\x00-\x7F]+', ' ', title_text)
    
    print(f"Window class: {cls}")
    print(f"Grid ID: {grid_id}")
    print(f"Header Title: {title_text}")
    print("-" * 40)
