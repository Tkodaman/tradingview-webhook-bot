import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

latest_edits = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'replace_file_content' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        if '2026-09-11' <= created_at:
                            for tc in data['tool_calls']:
                                name = tc.get('name', '')
                                if 'replace_file_content' in name:
                                    args = tc.get('args', tc.get('arguments', {}))
                                    if isinstance(args, str):
                                        args = json.loads(args)
                                    target = args.get('TargetFile', '')
                                    if 'dashboard.html' in target:
                                        latest_edits.append((created_at, f))
    except Exception as e:
        pass

latest_edits.sort()
for e in latest_edits:
    print(e)
