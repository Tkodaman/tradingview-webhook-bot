with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find("You're in planning mode. Exercise judgement")
if idx != -1:
    print("Found garbage at index:", idx)
    # Find the bounds of this panel
    idx_start = text.rfind('<div class="panel"', 0, idx)
    idx_end = text.find('</div>\n        </div>', idx)
    if idx_start != -1 and idx_end != -1:
        print(text[idx_start:idx_end+14].encode('ascii', 'ignore').decode('ascii'))
