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
                    if 'tool_calls' in data:
                        found_model = True
                    continue
                
                if found_model and data.get('source') == 'SYSTEM':
                    print("Type:", data.get('type'))
                    print("Keys:", data.keys())
                    if data.get('type') == 'TOOL_RESPONSE':
                        if 'tool_responses' in data:
                            for tr in data['tool_responses']:
                                print("TOOL RESPONSE KEYS:", tr.keys())
                                if 'content' in tr:
                                    content = tr['content']
                                    if len(content) > 1000: # it's a file
                                        with open('dashboard_from_chat_real.html', 'w', encoding='utf-8') as out:
                                            out.write('\n'.join(content.split('\n')[2:]))
                                        print("SAVED FILE!")
                                        import sys
                                        sys.exit(0)
                        
    except Exception as e:
        pass
