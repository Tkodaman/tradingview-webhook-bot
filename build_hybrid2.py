with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    dash = f.read()

start = dash.find('const wsUrl = ws:///ws/live;')
end = dash.find('// Modal functions', start)
if end == -1:
    end = dash.find('function updateChartData', start)
if end == -1:
    end = dash.find('</script>', start)

ws_block = dash[start:end].strip()

with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    cand = f.read()

cand = cand.replace('// LLM blink animation', ws_block + '\n\n// LLM blink animation')

# ALSO fix the <script> tags!
# cand_5b4e9.html had the missing <script> tags issue!
# Let's just ensure there is a <script> before the first function!
# And </script> before </body>!
if '<script>' not in cand[cand.find('window.onerror'):cand.find('window.onerror')+1000]:
    cand = cand.replace('window.onerror = function(msg', '<script>\nwindow.onerror = function(msg', 1)

with open('templates/dashboard_hybrid.html', 'w', encoding='utf-8') as f:
    f.write(cand)

print("Saved dashboard_hybrid.html! WS length:", len(ws_block))
