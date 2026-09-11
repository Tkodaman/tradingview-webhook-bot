import os
import json

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'

transcripts = []
for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file == 'transcript_full.jsonl':
            transcripts.append(os.path.join(root, file))

print('Found', len(transcripts), 'transcripts')

matches = []

for t_path in transcripts:
    try:
        with open(t_path, 'r', encoding='utf-8') as f:
            for line in f:
                if 'dashboard.html' in line:
                    data = json.loads(line)
                    created_at = data.get('created_at', 'unknown_time')
                    
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            args = tc.get('arguments', {})
                            if tc.get('name') in ['default_api:write_to_file', 'default_api:replace_file_content', 'default_api:multi_replace_file_content']:
                                if 'dashboard.html' in args.get('TargetFile', ''):
                                    matches.append((t_path, created_at, 'WRITE/EDIT', len(args.get('CodeContent', '') or args.get('ReplacementContent', ''))))
                                
                    if data.get('type') == 'TOOL_RESPONSE' or data.get('type') == 'SYSTEM':
                        if 'dashboard.html' in str(data.get('content', '')):
                            content_len = len(str(data.get('content', '')))
                            matches.append((t_path, created_at, 'READ/RESP', content_len))
                            
    except Exception as e:
        print('Error in', t_path, e)

matches.sort(key=lambda x: str(x[1]))
print('Found matches:', len(matches))
for m in matches[-50:]:
    print(m)
