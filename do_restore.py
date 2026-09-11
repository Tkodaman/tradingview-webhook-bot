import json
import glob
import os

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
                    
                    # If it's a TOOL_RESPONSE from view_file or similar
                    if 'content' in data:
                        content = data['content']
                        if type(content) == str and '<!DOCTYPE html>' in content and '</html>' in content:
                            idx1 = content.find('<!DOCTYPE html>')
                            idx2 = content.find('</html>', idx1) + 7
                            html = content[idx1:idx2]
                            if 'TRADINGVIEW' in html:
                                html_versions.append((created_at, html))
                    
                    # If it's a PLANNER_RESPONSE with write_to_file
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            args = tc.get('arguments', {})
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except:
                                    pass
                            if isinstance(args, dict):
                                content = args.get('CodeContent', '') or args.get('ReplacementContent', '')
                                if '<!DOCTYPE html>' in content and '</html>' in content:
                                    idx1 = content.find('<!DOCTYPE html>')
                                    idx2 = content.find('</html>', idx1) + 7
                                    html = content[idx1:idx2]
                                    if 'TRADINGVIEW' in html:
                                        html_versions.append((created_at, html))

    except Exception as e:
        pass

html_versions.sort(key=lambda x: x[0])

if html_versions:
    best_html = html_versions[-1][1]
    with open(r'templates\dashboard.html', 'w', encoding='utf-8') as out:
        out.write(best_html)
    print("RESTORED DASHBOARD FROM: ", html_versions[-1][0])
    print("SIZE: ", len(best_html))
else:
    print("NOT FOUND")
