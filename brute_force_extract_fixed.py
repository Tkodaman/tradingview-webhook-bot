import json
import glob
import os
import re

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

all_text = ""
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            all_text += file.read()
    except Exception as e:
        pass

# Find all indices of <!DOCTYPE html>
start_indices = [m.start() for m in re.finditer(r'<!DOCTYPE html>', all_text)]
html_versions = []

for start in start_indices:
    end = all_text.find('</html>', start)
    if end != -1:
        html = all_text[start:end+7]
        if 'TRADINGVIEW' in html or 'TradingView' in html or 'TRADINGVIEW' in html.replace('\\n', ''):
            html_versions.append(html)

print("Valid TradingView matches:", len(html_versions))

if html_versions:
    # Sort by length
    html_versions.sort(key=lambda x: len(x))
    
    # Let's check the lengths of the top 5
    print("Lengths of top 5:", [len(x) for x in html_versions[-5:]])
    
    best = html_versions[-1]
    
    # decode escapes
    best = best.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
    
    # also try to decode \u escapes if it's still a JSON string representation
    try:
        best = best.encode('utf-8').decode('unicode_escape')
    except:
        pass
    
    with open('templates/dashboard_restored.html', 'w', encoding='utf-8') as out:
        out.write(best)
    print("Saved to templates/dashboard_restored.html")
