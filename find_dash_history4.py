import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

modifications = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'dashboard.html' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        if '2026-09-03' <= created_at < '2026-09-11':
                            for tc in data['tool_calls']:
                                args = tc.get('args', {})
                                if 'dashboard.html' in str(args):
                                    modifications.append(created_at + ' ' + tc.get('name'))
    except Exception as e:
        pass

modifications.sort()
for m in modifications:
    print(m)
