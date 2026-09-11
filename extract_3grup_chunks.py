import json
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = [
    r'C:\Users\ASUS\.gemini\antigravity-ide\brain\20d37064-7471-4d59-bb3e-40ec2c15b4e9\.system_generated\logs\transcript_full.jsonl'
]

# We want the chunks from 2026-09-03T21:02:24Z for dashboard.html
target_time = '2026-09-03T21:02:24Z'
found = False

for f in files:
    if not os.path.exists(f): continue
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
                                chunks = args.get('ReplacementChunks', [])
                                print(f"Found {len(chunks)} chunks!")
                                for i, chunk in enumerate(chunks):
                                    print(f"\n--- CHUNK {i} ---")
                                    print("TARGET:")
                                    print(chunk.get('TargetContent', '')[:200])
                                    print("\nREPLACEMENT:")
                                    print(chunk.get('ReplacementContent', '')[:200])
                                found = True
if not found:
    print("Could not find the chunks!")
