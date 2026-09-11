import json
import glob
import os
import re

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

# We want to trace the content of dashboard.html up to 2026-09-11 01:00:00 UTC
# Actually the user's local time was 00:10.
# We will just print the timestamps of when dashboard.html was modified.

modifications = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'dashboard.html' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        for tc in data['tool_calls']:
                            name = tc.get('name')
                            args = tc.get('arguments', {})
                            if name in ['default_api:write_to_file', 'default_api:replace_file_content', 'default_api:multi_replace_file_content']:
                                target = args.get('TargetFile', '')
                                if 'dashboard.html' in target:
                                    modifications.append({
                                        'time': created_at,
                                        'tool': name,
                                        'args': args
                                    })
    except Exception as e:
        pass

modifications.sort(key=lambda x: x['time'])
print(f"Found {len(modifications)} modifications to dashboard.html.")
for m in modifications:
    print(m['time'], m['tool'])

