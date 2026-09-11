with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_start = text.find('15 Momentum')
idx_container = text.rfind('<div class="panel-container"', 0, idx_start)
idx_end = text.find('<div class="panel-container"', idx_start)

if idx_container != -1 and idx_end != -1:
    top15 = text[idx_container:idx_end]
    with open('top15_block.html', 'w', encoding='utf-8') as f:
        f.write(top15)
    print("Extracted Top 15 block successfully.")
else:
    print("Could not extract.")
