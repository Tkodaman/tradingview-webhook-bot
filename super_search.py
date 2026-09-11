import json
import glob
import os
import datetime

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

candidates = []

for f in files:
    mtime = os.path.getmtime(f)
    dt = datetime.datetime.fromtimestamp(mtime)
    
    # We want transcripts from Sept 9 to Sept 11 01:15
    if dt < datetime.datetime(2026, 9, 11, 1, 15):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                for line in file:
                    if 'dashboard.html' in line:
                        data = json.loads(line)
                        created_at = data.get('created_at', '')
                        
                        # recursively search for large strings in the JSON object
                        def search_strings(obj):
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    search_strings(v)
                            elif isinstance(obj, list):
                                for item in obj:
                                    search_strings(item)
                            elif isinstance(obj, str):
                                if len(obj) > 10000 and '<!DOCTYPE html>' in obj and 'TRADINGVIEW' in obj.replace('\\n', '').upper():
                                    candidates.append((created_at, f, obj))
                        
                        search_strings(data)
        except Exception as e:
            pass

candidates.sort(key=lambda x: x[0])

print(f"Found {len(candidates)} candidate HTML strings.")
if candidates:
    best = candidates[-1]
    print("Latest HTML is from:", best[0], "in file", best[1])
    html = best[2]
    if '</html>' in html:
        idx = html.find('</html>') + 7
        html = html[:idx]
    
    with open('templates/dashboard_found.html', 'w', encoding='utf-8') as out:
        out.write(html)
    print("Saved to templates/dashboard_found.html")
