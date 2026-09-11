import json
import glob
import os
import hashlib

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

cand_hash = ''
with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
    # Normalize line endings just in case
    cand_hash = hashlib.md5(text.replace('\r\n', '\n').encode('utf-8')).hexdigest()

print("Cand hash:", cand_hash)

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                data = json.loads(line)
                if data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
                    if 'tool_responses' in data:
                        for tr in data['tool_responses']:
                            content = tr.get('content', '')
                            # Strip tool prefix
                            lines = content.split('\n')
                            if len(lines) > 2:
                                file_content = '\n'.join(lines[2:])
                                file_hash = hashlib.md5(file_content.replace('\r\n', '\n').encode('utf-8')).hexdigest()
                                if file_hash == cand_hash:
                                    print("FOUND MATCH!")
                                    print("File:", f)
                                    print("Time:", data.get('created_at'))
    except Exception as e:
        pass
