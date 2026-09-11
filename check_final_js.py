with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import sys
sys.stdout.reconfigure(encoding='utf-8')
idx = text.find('function renderHeatmapBoxes')
print(text[idx:idx+1500])
