import json
import glob
import os
import datetime

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

writes = []

for f in files:
    mtime = os.path.getmtime(f)
    dt = datetime.datetime.fromtimestamp(mtime)
    
    if dt < datetime.datetime(2026, 9, 11, 2, 0):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                for line in file:
                    if 'write_to_file' in line or 'replace_file_content' in line or 'multi_replace_file_content' in line:
                        data = json.loads(line)
                        created_at = data.get('created_at', '')
                        for tc in data.get('tool_calls', []):
                            args = tc.get('arguments', {})
                            if isinstance(args, str):
                                try: args = json.loads(args)
                                except: pass
                            if isinstance(args, dict):
                                target = args.get('TargetFile', '')
                                if '.py' in target:
                                    content = args.get('CodeContent', '')
                                    if len(content) > 1000:
                                        writes.append((created_at, target, len(content)))
                                    if 'ReplacementChunks' in args:
                                        chunks = args['ReplacementChunks']
                                        if isinstance(chunks, str):
                                            try: chunks = json.loads(chunks)
                                            except: pass
                                        if isinstance(chunks, list):
                                            for chunk in chunks:
                                                rc = chunk.get('ReplacementContent', '')
                                                if len(rc) > 1000:
                                                    writes.append((created_at, target, len(rc)))
        except Exception as e:
            pass

writes.sort(key=lambda x: x[0])
for w in writes[-20:]:
    print(w[0], w[1], "Size:", w[2])
