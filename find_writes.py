import json
import glob
import os
import datetime

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

candidates = []

for f in files:
    mtime = os.path.getmtime(f)
    dt = datetime.datetime.fromtimestamp(mtime)
    
    if dt < datetime.datetime(2026, 9, 11, 2, 0):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                for line in file:
                    if 'tool_calls' in line:
                        data = json.loads(line)
                        created_at = data.get('created_at', '')
                        for tc in data.get('tool_calls', []):
                            args = tc.get('arguments', {})
                            if isinstance(args, str):
                                try: args = json.loads(args)
                                except: pass
                            if isinstance(args, dict):
                                for k, v in args.items():
                                    if isinstance(v, str) and len(v) > 20000 and '<!DOCTYPE html>' in v:
                                        candidates.append((created_at, f, len(v), v))
                                        
                                # Also check ReplacementChunks
                                if 'ReplacementChunks' in args:
                                    chunks = args['ReplacementChunks']
                                    if isinstance(chunks, str):
                                        try: chunks = json.loads(chunks)
                                        except: pass
                                    if isinstance(chunks, list):
                                        for chunk in chunks:
                                            rc = chunk.get('ReplacementContent', '')
                                            if len(rc) > 20000 and '<!DOCTYPE html>' in rc:
                                                candidates.append((created_at, f, len(rc), rc))
        except Exception as e:
            pass

candidates.sort(key=lambda x: x[0])
print(f"Found {len(candidates)} large HTML write tool calls.")
for c in candidates:
    print(c[0], c[1][-50:], "Size:", c[2])

if candidates:
    html = candidates[-1][3]
    with open('templates/dashboard_candidate.html', 'w', encoding='utf-8') as f:
        f.write(html)
