with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_start = text.find('<div class="panel-container">')
idx_end = text.find('<div class="panel-container" style="display:flex;')

if idx_start != -1 and idx_end != -1:
    top15 = text[idx_start:idx_end]
    with open('top15_block.html', 'w', encoding='utf-8') as f:
        f.write(top15)
    print("Extracted Top 15 block successfully.")
else:
    print("Could not find Top 15 block.")
