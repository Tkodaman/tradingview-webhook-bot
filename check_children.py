import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('MAIN DASHBOARD LAYOUT')
start = text.find('<div style="display: flex; gap: 24px', idx)
end = text.find('<!-- END MAIN DASHBOARD GRID -->', start)

if start != -1 and end != -1:
    content = text[start:end]
    # Let's count direct children of this flex container
    level = 0
    children = []
    current_child_start = -1
    
    # Simple regex to find top-level divs inside the flex container
    # Since parsing HTML is hard, I will just print the first 200 chars of each child
    print("Children of main flex container:")
    matches = re.finditer(r'<div[^>]*style="flex:', content)
    for m in matches:
        print(m.group(0))

