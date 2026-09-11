import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'function renderHeatmapBoxes[\s\S]*?\}', text)
if match:
    print(match.group(0))
