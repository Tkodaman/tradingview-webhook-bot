import json
import glob
import os
import re

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

found = False
for f in files:
    if not found:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                for line in file:
                    if '<!DOCTYPE html>' in line:
                        data = json.loads(line)
                        if 'content' in data:
                            c = str(data['content'])
                            if '<!DOCTYPE html>' in c and '</html>' in c:
                                idx1 = c.find('<!DOCTYPE html>')
                                idx2 = c.find('</html>', idx1) + 7
                                html = c[idx1:idx2]
                                if len(html) < 200000: # reasonable size
                                    if 'TRADINGVIEW' in html or 'TradingView' in html or 'TRADINGVIEW' in html.replace('\\n', ''):
                                        print(f"Found HTML of size {len(html)} in {f}")
                                        html = html.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                                        try: html = html.encode('utf-8').decode('unicode_escape')
                                        except: pass
                                        with open('templates/dashboard_found.html', 'w', encoding='utf-8') as out:
                                            out.write(html)
                                        found = True
                                        break
        except Exception as e:
            pass
