with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_aktif = text.find('Aktif Açık')
if idx_aktif == -1: idx_aktif = text.find('Aktif A')
idx_top15 = text.find('Top 15')

print(f"Aktif index: {idx_aktif}")
print(f"Top15 index: {idx_top15}")

# We must swap them if Top 15 is before Aktif!
if idx_top15 < idx_aktif and idx_top15 != -1 and idx_aktif != -1:
    # They need swapping
    main_grid_start = text.rfind('<div class="main-grid"', 0, idx_top15)
    main_grid_end = text.find('<!-- RIGHT CONTENT (Live Log) -->', main_grid_start)
    if main_grid_start != -1 and main_grid_end != -1:
        main_grid_content = text[main_grid_start:main_grid_end]
        
        top15_start = main_grid_content.find('<div class="panel-container">')
        aktif_start = main_grid_content.find('<div class="panel-container" style="display:flex;')
        
        if top15_start != -1 and aktif_start != -1:
            top15_html = main_grid_content[top15_start:aktif_start]
            aktif_end = main_grid_content.rfind('</div>', 0, len(main_grid_content)-10) + 6
            aktif_html = main_grid_content[aktif_start:aktif_end]
            
            new_main_grid = main_grid_content[:top15_start] + aktif_html + "\n" + top15_html + "\n</div>\n    </div>\n    \n    "
            
            text = text.replace(main_grid_content, new_main_grid)
            
            with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
                f.write(text)
            print("Swapped successfully!")
        else:
            print("Could not find panel containers inside main grid.")
    else:
        print("Could not find main grid boundaries.")
else:
    print("No swap needed.")
