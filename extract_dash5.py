import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

found_model = False
target_id = None

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                data = json.loads(line)
                
                if data.get('created_at') == '2026-09-10T21:43:35Z' and data.get('source') == 'MODEL':
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            if tc.get('name') == 'default_api:view_file':
                                target_id = tc.get('id')
                                print("Found tool_call id:", target_id)
                
                if target_id and data.get('source') == 'SYSTEM' and 'tool_calls' in data:
                    # In some transcript formats, the system response returns a tool_calls list matching the id
                    for tc in data['tool_calls']:
                        if tc.get('id') == target_id:
                            content = tc.get('output', '')
                            with open('dashboard_restored_from_chat.html', 'w', encoding='utf-8') as out:
                                out.write(str(content))
                            print("Wrote output!")
                            import sys
                            sys.exit(0)
    except Exception as e:
        pass
