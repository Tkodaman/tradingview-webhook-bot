import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'Kripto Piyasası' in line:
                    data = json.loads(line)
                    print(f"File: {f}")
                    print(f"Created: {data.get('created_at')}")
                    print(f"Source: {data.get('source')}")
                    print(f"Type: {data.get('type')}")
                    if data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
                        # it's a tool response
                        pass
    except Exception as e:
        pass
