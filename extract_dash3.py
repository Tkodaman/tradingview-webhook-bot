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
                    content = data.get('content', '')
                    # Content starts with something like:
                    # Tool default_api:view_file returned:
                    # [File contents here]
                    # We can try to parse out the file content.
                    
                    lines = content.split('\n')
                    if len(lines) > 2:
                        file_content = '\n'.join(lines[2:]) # Skip the first two lines usually
                        with open('dashboard_restored_from_chat.html', 'w', encoding='utf-8') as out:
                            out.write(file_content)
                        print("Saved dashboard_restored_from_chat.html!")
                    break
    except Exception as e:
        pass
