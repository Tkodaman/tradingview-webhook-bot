import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            found_model = False
            for line in file:
                data = json.loads(line)
                
                if data.get('created_at') == '2026-09-10T21:43:35Z' and data.get('source') == 'MODEL':
                    found_model = True
                    continue
                
                if found_model and data.get('source') == 'SYSTEM':
                    print("SYSTEM response keys:", data.keys())
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            print("SYSTEM tool_call keys:", tc.keys())
                            if 'output' in tc:
                                print(str(tc['output'])[:500])
                    break
    except Exception as e:
        pass

