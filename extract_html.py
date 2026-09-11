import json
import glob
import os

paths = glob.glob(r'C:\Users\ASUS\.gemini\antigravity-ide\brain\*\.system_generated\logs\transcript_full.jsonl')

html_versions = []

for p in paths:
    try:
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                if '<!DOCTYPE html>' in line and 'TRADINGVIEW' in line:
                    data = json.loads(line)
                    created_at = data.get('created_at', '')
                    
                    # Search inside tool_calls (write_to_file / replace_file_content)
                    if 'tool_calls' in data:
                        for tc in data['tool_calls']:
                            args = tc.get('arguments', {})
                            content = args.get('CodeContent', '') or args.get('ReplacementContent', '')
                            if '<!DOCTYPE html>' in content and len(content) > 10000:
                                html_versions.append((created_at, p, len(content), content))
                    
                    # Search inside content (view_file)
                    if 'content' in data:
                        content = data['content']
                        if '<!DOCTYPE html>' in content and len(content) > 10000:
                            html_versions.append((created_at, p, len(content), content))
    except Exception as e:
        pass

html_versions.sort(key=lambda x: x[0])

for v in html_versions[-10:]:
    print("Time:", v[0], "| File:", os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(v[1])))), "| Size:", v[2])

if html_versions:
    best_content = html_versions[-1][3]
    # Try to extract just the HTML part from the view_file output if necessary
    idx = best_content.find('<!DOCTYPE html>')
    html_only = best_content[idx:]
    with open('dashboard_restored_from_chat.html', 'w', encoding='utf-8') as f:
        f.write(html_only)
    print("Saved the latest found HTML to dashboard_restored_from_chat.html")
