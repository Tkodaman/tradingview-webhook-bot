with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# The ws block starts with const wsUrl and ends somewhere.
# Let's find the full boundaries.
start = text.find('const wsUrl = ws:///ws/live;')
# The block ends before the sync function fetchMarketStatus() or something.
end = text.find('async function fetchBotHealth()', start)
if end == -1:
    end = text.find('// LLM blink animation', start)
if end == -1:
    end = text.find('</script>', start)

ws_block = text[start:end]
with open('ws_block.js', 'w', encoding='utf-8') as f:
    f.write(ws_block)
print("Saved ws block of length", len(ws_block))
