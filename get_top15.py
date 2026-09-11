with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('Top 15')
if idx != -1:
    start = text.rfind('<div class="panel-container"', 0, idx)
    # The end is right before the next panel-container
    end = text.find('<div class="panel-container"', idx)
    if start != -1 and end != -1:
        with open('top15_block.html', 'w', encoding='utf-8') as f:
            f.write(text[start:end])
        print("Extracted top 15")
