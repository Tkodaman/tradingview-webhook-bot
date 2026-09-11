import json
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
# Find the latest transcript file in all brains
import glob
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

target_time = '2026-09-03T21:02:24Z'
found = False

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        for line in file:
            if target_time in line and 'replace_file_content' in line:
                data = json.loads(line)
                if data.get('created_at') == target_time:
                    for tc in data['tool_calls']:
                        if 'replace_file_content' in tc['name']:
                            args = tc.get('args', tc.get('arguments', {}))
                            if isinstance(args, str): args = json.loads(args)
                            
                            target = args.get('TargetFile', '')
                            if 'dashboard.html' in target:
                                print("FOUND IT!")
                                rep_content = args.get('ReplacementContent', '')
                                print(rep_content[:500])
                                # Save the replacement content so I can inspect it
                                with open('3grup_content.txt', 'w', encoding='utf-8') as out:
                                    out.write(rep_content)
                                found = True
if not found:
    print("Still could not find it")
