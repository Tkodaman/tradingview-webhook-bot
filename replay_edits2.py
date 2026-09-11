import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))

edits = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'replace_file_content' in line:
                    data = json.loads(line)
                    if data.get('source') == 'MODEL' and 'tool_calls' in data:
                        created_at = data.get('created_at', '')
                        if '2026-09-03' <= created_at <= '2026-09-10T22:57:00Z':
                            for tc in data['tool_calls']:
                                name = tc.get('name', '')
                                if 'replace_file_content' in name:
                                    args = tc.get('args', tc.get('arguments', {}))
                                    if isinstance(args, str):
                                        args = json.loads(args)
                                    target = args.get('TargetFile', '')
                                    if 'dashboard.html' in target:
                                        edits.append({
                                            'time': created_at,
                                            'name': name,
                                            'args': args
                                        })
    except Exception as e:
        pass

edits.sort(key=lambda x: x['time'])
print(f"Found {len(edits)} edits to dashboard.html.")
for e in edits:
    print(e['time'], e['name'])

with open('temp_sept3.html', 'r', encoding='utf-16', errors='ignore') as f:
    content = f.read()

# I will write a simple string replacer for the edits.
for edit in edits:
    args = edit['args']
    if edit['name'] == 'default_api:replace_file_content':
        target = args.get('TargetContent', '')
        replacement = args.get('ReplacementContent', '')
        content = content.replace(target, replacement)
    elif edit['name'] == 'default_api:multi_replace_file_content':
        for chunk in args.get('ReplacementChunks', []):
            target = chunk.get('TargetContent', '')
            replacement = chunk.get('ReplacementContent', '')
            content = content.replace(target, replacement)

with open('dashboard_rebuilt_properly.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Rebuilt file saved to dashboard_rebuilt_properly.html!")
