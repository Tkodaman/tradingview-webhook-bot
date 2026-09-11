import json
import glob
import os
import re

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

for f in files:
    mtime = os.path.getmtime(f)
    if mtime < 1789230000: # before Sept 12
        try:
            with open(f, 'r', encoding='utf-8') as file:
                all_text = file.read()
            
            start_indices = [m.start() for m in re.finditer(r'<!DOCTYPE html>', all_text)]
            for start in start_indices:
                end = all_text.find('</html>', start)
                if end != -1:
                    html = all_text[start:end+7]
                    if len(html) < 200000 and 'TRADINGVIEW' in html.replace('\\n', '').upper():
                        print(f"Found {len(html)} bytes in {f[-50:]}")
                        # save it temporarily to see if it's the one
                        with open('templates/cand_' + f[-50:-45] + '.html', 'w', encoding='utf-8') as out:
                            # basic unescape just to read it
                            unescaped = html.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                            out.write(unescaped)
        except Exception as e:
            pass
