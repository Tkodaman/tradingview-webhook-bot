import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

found_tool_call_id = None
content = None

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                data = json.loads(line)
                
                if data.get('created_at') == '2026-09-10T21:43:35Z' and data.get('source') == 'MODEL':
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            if tc.get('name') == 'default_api:view_file':
                                found_tool_call_id = tc.get('id')
                
                if found_tool_call_id and data.get('source') == 'SYSTEM':
                    # Looking for the system response matching this tool call id
                    # In some transcript formats, the tool_responses are tracked by tool_call_id
                    if 'tool_responses' in data:
                        for tr in data['tool_responses']:
                            if tr.get('tool_call_id') == found_tool_call_id:
                                content = tr.get('content')
                                break
                    if content: break
    except Exception as e:
        pass

if content:
    with open('dashboard_restored_from_chat.html', 'w', encoding='utf-8') as out:
        out.write(content)
    print("Successfully extracted dashboard.html from 21:43:35Z!")
else:
    print("Could not find the content.")
