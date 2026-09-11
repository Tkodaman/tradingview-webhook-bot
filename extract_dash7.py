import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            found_model = False
            tool_call_id = None
            for line in file:
                data = json.loads(line)
                
                # Check for the model call that issued view_file
                if data.get('created_at') == '2026-09-10T21:43:35Z' and data.get('source') == 'MODEL':
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            if tc.get('name') == 'default_api:view_file':
                                found_model = True
                                tool_call_id = tc.get('id')
                    continue
                
                if found_model and data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
                    if tool_call_id is None or data.get('tool_call_id') == tool_call_id:
                        content = data.get('content', '')
                        lines = content.split('\n')
                        file_content = '\n'.join(lines[2:]) # Skip the first two lines usually
                        with open('dashboard_from_chat_final.html', 'w', encoding='utf-8') as out:
                            out.write(file_content)
                        print("Saved dashboard_from_chat_final.html!")
                        import sys
                        sys.exit(0)
    except Exception as e:
        pass
