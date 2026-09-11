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
                if data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
                    if 'tool_responses' in data:
                        for tr in data['tool_responses']:
                            content = tr.get('content', '')
                            if 'Kripto Piyasası' in content and 'dashboard.html' in content:
                                print("FOUND AT:", data.get('created_at'), "in", f)
    except Exception as e:
        pass
