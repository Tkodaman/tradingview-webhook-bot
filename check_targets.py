import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

targets = set()
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'replace_file_content' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            if 'replace_file_content' in tc.get('name', ''):
                                args = tc.get('args', tc.get('arguments', {}))
                                target = args.get('TargetFile', '')
                                targets.add(target)
    except Exception as e:
        pass

for t in targets:
    print(t)
