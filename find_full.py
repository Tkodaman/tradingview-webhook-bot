import json
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain\456e22e9-0bf5-47c3-a3df-2e9c6bdf32ff'
transcript_path = os.path.join(brain_dir, '.system_generated', 'logs', 'transcript_full.jsonl')

# I will find the EXACT replace_file_content chunk where the 3 groups were introduced!
# We found it at '2026-09-03T21:02:24Z' earlier, but let me search transcript_full.jsonl for all 'replace_file_content' of 'dashboard.html'.
# I'll look for 'market-window-crypto'

latest_html = ""
with open(transcript_path, 'r', encoding='utf-8') as file:
    for line in file:
        if 'replace_file_content' in line and 'market-window-crypto' in line:
            data = json.loads(line)
            if data.get('source') == 'MODEL' and 'tool_calls' in data:
                for tc in data['tool_calls']:
                    if 'replace_file_content' in tc['name']:
                        args = tc.get('args', tc.get('arguments', {}))
                        if isinstance(args, str): args = json.loads(args)
                        target = args.get('TargetFile', '')
                        if 'dashboard.html' in target:
                            latest_html = args.get('ReplacementContent', '')
                            
if latest_html:
    with open('templates/cand_full.html', 'w', encoding='utf-8') as f:
        f.write(latest_html)
    print("Found and saved cand_full.html! Length:", len(latest_html))
else:
    print("Not found in current conversation.")
