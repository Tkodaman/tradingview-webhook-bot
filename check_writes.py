import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

writes = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'write_to_file' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        if '2026-09-03' <= created_at <= '2026-09-11T01:30:00Z':
                            for tc in data['tool_calls']:
                                name = tc.get('name', '')
                                if 'write_to_file' in name:
                                    args = tc.get('args', tc.get('arguments', {}))
                                    if isinstance(args, str):
                                        args = json.loads(args)
                                    target = args.get('TargetFile', '')
                                    if 'dashboard.html' in target:
                                        writes.append((created_at, target))
    except Exception as e:
        pass

writes.sort()
for w in writes:
    print(w)
