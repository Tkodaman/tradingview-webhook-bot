import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if '2026-09-10T21:43:35Z' in line and 'view_file' in line:
                    print(line[:500])
                    print("...")
                    
                    data = json.loads(line)
                    if 'tool_calls' in data:
                        tc = data['tool_calls'][0]
                        print("ID:", tc.get('id', 'No ID'))
    except Exception as e:
        pass
