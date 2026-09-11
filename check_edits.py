import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

edits = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'replace_file_content' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        if '2026-09-03' <= created_at <= '2026-09-10T22:57:00Z':
                            for tc in data['tool_calls']:
                                name = tc.get('name', '')
                                if 'replace_file_content' in name:
                                    args = tc.get('args', tc.get('arguments', {}))
                                    # check if TargetFile has dashboard.html
                                    target = args.get('TargetFile', '')
                                    if 'dashboard.html' in target:
                                        edits.append((created_at, name))
    except Exception as e:
        pass

edits.sort()
for e in edits:
    print(e)
