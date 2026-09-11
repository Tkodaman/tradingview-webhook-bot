import re

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    dash = f.read()

with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    cand = f.read()

# Extract WS block from dashboard.html
ws_start = dash.find('const wsUrl = ws:///ws/live;')
ws_end = dash.find('// Sayfa y\u00fcklendi\u011finde', ws_start)
if ws_end == -1:
    ws_end = dash.find('// LLM blink animation', ws_start)
if ws_end == -1:
    ws_end = dash.find('function showToast', ws_start)
if ws_end == -1:
    ws_end = dash.find('</script>', ws_start)

ws_block = dash[ws_start:ws_end].strip()

# Clean up any bad template literals (the  bug) in ws_block
ws_block = re.sub(r'\$\$\{', '${', ws_block)
ws_block = re.sub(r'toFixed\(2\)\};', 'toFixed(2)};', ws_block)
ws_block = ws_block.replace("}</span></td>", "}")
# Remove any 'const wsUrl' that might have been accidentally commented out
# Actually wait, ws_block shouldn't have  syntax errors if it's the stable dashboard, but let's be safe.

# Insert WS block into cand
marker = "// ================================================================\n        // 🚀 WEBSOCKET CANLI PİYASA AKIŞI\n        // ================================================================"
if marker in cand:
    cand = cand.replace(marker, marker + '\n\n' + ws_block + '\n')
else:
    # try another marker
    marker2 = "// \ud83d\ude80 WEBSOCKET CANLI P\u0130YASA AKI\u015eI"
    idx = cand.find(marker2)
    if idx != -1:
        end_idx = cand.find('\n', idx)
        cand = cand[:end_idx+1] + '\n' + ws_block + '\n' + cand[end_idx+1:]
    else:
        # Just put it before the closing script
        cand = cand.replace('// LLM blink animation', ws_block + '\n\n// LLM blink animation')

with open('templates/dashboard_hybrid.html', 'w', encoding='utf-8') as f:
    f.write(cand)

print("Saved dashboard_hybrid.html! WS length:", len(ws_block))
