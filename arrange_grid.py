with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# I will find the main-grid
start = text.find('<div class="main-grid"')
end = text.find('<!-- RIGHT CONTENT', start)

if start != -1 and end != -1:
    main_grid = text[start:end]
    
    # We want to make sure Aktif is first, Top 15 is second.
    # The current order is likely Top 15 then Aktif.
    
    # Let's find Top 15
    top15_idx = main_grid.find('Top 15')
    if top15_idx != -1:
        top15_start = main_grid.rfind('<div class="panel-container"', 0, top15_idx)
        # Find the next panel-container
        next_panel = main_grid.find('<div class="panel-container"', top15_idx)
        if next_panel != -1:
            top15_content = main_grid[top15_start:next_panel]
            aktif_content = main_grid[next_panel:]
            
            # The closing of main_grid might be at the end of aktif_content.
            # Wait, main_grid has closing divs. Let's not mess up the closing divs.
            # I will just write a simpler regex.
            pass
