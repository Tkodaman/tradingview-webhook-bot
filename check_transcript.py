import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'replace_file_content' in line or 'write_to_file' in line:
                    data = json.loads(line)
                    print("Structure of tool_calls:")
                    if 'tool_calls' in data:
                        print(type(data['tool_calls']), type(data['tool_calls'][0]))
                        print(data['tool_calls'][0].keys())
                    break
    except Exception as e:
        pass
