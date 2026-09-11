import json
import glob
import os
import re

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
                        for tc in data['tool_calls']:
                            name = tc.get('name', '')
                            args = tc.get('args', {})  # the keys are 'name' and 'args' based on check_transcript!
                            args_str = str(args)
                            if 'dashboard.html' in args_str:
                                modifications.append({
                                    'time': created_at,
                                    'tool': name,
                                    'args': str(args)[:100] + '...' # Just a snippet
                                })
    except Exception as e:
        pass

modifications.sort(key=lambda x: x['time'])
for m in modifications:
    print(m['time'], m['tool'])
    print(m['args'])
