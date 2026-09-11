import json
import re

f = r'C:\Users\ASUS\.gemini\antigravity-ide\brain\75113ff5-b6f9-4032-8247-0748a5f81486\.system_generated\logs\transcript_full.jsonl'

try:
    with open(f, 'r', encoding='utf-8') as file:
        all_text = file.read()
except Exception as e:
    print("Error:", e)

start_indices = [m.start() for m in re.finditer(r'<!DOCTYPE html>', all_text)]
html_versions = []

for start in start_indices:
    end = all_text.find('</html>', start)
    if end != -1:
        html = all_text[start:end+7]
        if len(html) < 200000 and 'TRADINGVIEW' in html:
            html_versions.append(html)

if html_versions:
    html_versions.sort(key=lambda x: len(x))
    best = html_versions[-1]
    best = best.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
    
    try:
        best = best.encode('utf-8').decode('unicode_escape')
    except:
        pass
        
    with open('templates/dashboard_restored.html', 'w', encoding='utf-8') as out:
        out.write(best)
    print("RESTORED! Length:", len(best))
else:
    print("No TradingView HTML found in this transcript!")
