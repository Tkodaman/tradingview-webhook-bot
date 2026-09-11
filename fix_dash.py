with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# Remove the bad injected block
# It starts at: function renderHeatmapBoxes
# It ends at: // RENDER SPECIFIC MARKET GROUP

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "function renderHeatmapBoxes(" in line:
        start_idx = i
    if "// RENDER SPECIFIC MARKET GROUP" in line:
        end_idx = i
        
if start_idx != -1 and end_idx != -1:
    lines_to_keep = lines[:start_idx] + lines[end_idx:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.writelines(lines_to_keep)
    print("Removed bad block.")
else:
    print("Could not find block boundaries.")
