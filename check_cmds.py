import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

commands = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'run_command' in line and 'dashboard.html' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        if '2026-09-10T22:57:00Z' <= created_at <= '2026-09-11T01:30:00Z':
                            for tc in data['tool_calls']:
                                name = tc.get('name', '')
                                if 'run_command' in name:
                                    args = tc.get('args', tc.get('arguments', {}))
                                    if isinstance(args, str):
                                        args = json.loads(args)
                                    cmd = args.get('CommandLine', '')
                                    if 'dashboard.html' in cmd:
                                        commands.append({
                                            'time': created_at,
                                            'cmd': cmd
                                        })
    except Exception as e:
        pass

commands.sort(key=lambda x: x['time'])
for c in commands:
    print(c['time'])
    print(c['cmd'])
    print("-" * 40)
