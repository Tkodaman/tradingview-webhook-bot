# -*- coding: utf-8 -*-
import os
import glob
import json

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

html_versions = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'dashboard.html' in line:
                    data = json.loads(line)
                    created_at = data.get('created_at', '')
                    
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            args = tc.get('arguments', {})
                            if 'dashboard.html' not in str(args): continue
                            
                            content = args.get('CodeContent', '') or args.get('ReplacementContent', '')
                            
                            chunks = args.get('ReplacementChunks', [])
                            if chunks:
                                for chunk in chunks:
                                    c = chunk.get('ReplacementContent', '')
                                    if '<!DOCTYPE html>' in c and '</html>' in c:
                                        html_versions.append((created_at, f, len(c), c))
                                        
                            if '<!DOCTYPE html>' in content and '</html>' in content:
                                html_versions.append((created_at, f, len(content), content))
                                
                    if 'content' in data:
                        c = str(data['content'])
                        if '<!DOCTYPE html>' in c and '</html>' in c:
                            idx1 = c.find('<!DOCTYPE html>')
                            idx2 = c.find('</html>', idx1) + 7
                            html = c[idx1:idx2]
                            if 'TRADINGVIEW' in html:
                                html_versions.append((created_at, f, len(html), html))
    except Exception as e:
        pass

html_versions.sort(key=lambda x: x[0])

for v in html_versions[-10:]:
    print("Time:", v[0], "| File:", os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(v[1])))), "| Size:", v[2])

if html_versions:
    html = html_versions[-1][3]
    html = html.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
    with open('best_found.html', 'w', encoding='utf-8') as out:
        out.write(html)
    print("Saved latest found HTML to best_found.html")
