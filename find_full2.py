import json
import os
import glob

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

latest_html = ""
latest_time = ""

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        for line in file:
            if 'replace_file_content' in line and 'market-window-crypto' in line:
                data = json.loads(line)
                if data.get('source') == 'MODEL' and 'tool_calls' in data:
                    created_at = data.get('created_at', '')
                    for tc in data['tool_calls']:
                        if 'replace_file_content' in tc['name']:
                            args = tc.get('args', tc.get('arguments', {}))
                            if isinstance(args, str): args = json.loads(args)
                            target = args.get('TargetFile', '')
                            if 'dashboard.html' in target:
                                latest_html = args.get('ReplacementContent', '')
                                latest_time = created_at
                                
if latest_html:
    with open('templates/cand_full.html', 'w', encoding='utf-8') as f:
        f.write(latest_html)
    print("Found cand_full.html from", latest_time, "Length:", len(latest_html))
else:
    print("Not found anywhere.")
