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
                
                if data.get('created_at') == '2026-09-10T22:56:44Z' and data.get('source') == 'MODEL':
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            if tc.get('name') == 'default_api:write_to_file':
                                args = tc.get('args', {})
                                if 'CodeContent' in args:
                                    with open('dashboard_written.html', 'w', encoding='utf-8') as out:
                                        out.write(args['CodeContent'])
                                    print("Saved dashboard_written.html!")
                                    import sys
                                    sys.exit(0)
    except Exception as e:
        pass
