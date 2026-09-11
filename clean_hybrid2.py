with open('templates/dashboard_hybrid.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_start = text.find('{"step_index":')
idx_style_end = text.find('</style>')

print("Junk start:", idx_start)
print("Style end:", idx_style_end)
print("Text between junk and style end:")
print(text[idx_start:idx_style_end][-500:])
