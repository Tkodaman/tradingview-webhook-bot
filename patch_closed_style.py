with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace inline style in renderHeatmapBoxes to be stronger
text = text.replace('const closedStyle = isOpen ? "" : "opacity: 0.5; filter: grayscale(80%);";', 'const closedStyle = isOpen ? "" : "opacity: 0.3; filter: grayscale(90%);";')

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Replaced successfully.")
