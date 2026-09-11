import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                data = json.loads(line)
                if data.get('created_at') == '2026-09-10T21:43:35Z' and data.get('source') == 'MODEL':
                    if 'tool_calls' in data:
                        print("MODEL sent tool_calls:", data['tool_calls'][0]['id'])
                        
                elif data.get('source') == 'SYSTEM' and 'tool_responses' in data:
                    for tr in data['tool_responses']:
                        if 'call_3uL6e5F6E3w2q8E3w2q8' in tr.get('tool_call_id', ''): # I need to know the id
                            pass
                    print("SYSTEM has tool_responses with ids:", [tr.get('tool_call_id') for tr in data['tool_responses']])
                    # just print the first one's content snippet
                    if '2026-09-10T21:43:3' in data.get('created_at', ''):
                        print("Tool response around 21:43:3x:")
                        print(data['tool_responses'][0]['content'][:100])
    except Exception as e:
        pass
