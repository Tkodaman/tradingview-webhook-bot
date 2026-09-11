import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript.jsonl'))

user_requests = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if 'USER_INPUT' in line:
                    data = json.loads(line)
                    if data.get('source') == 'USER_EXPLICIT' and 'content' in data:
                        created_at = data.get('created_at', '')
                        content = data['content']
                        # Sadece dashboard/arayüz/UI ile ilgili kelimeleri filtrele
                        if any(k in content.lower() for k in ['dashboard', 'arayüz', 'ui', 'pencere', 'buton', 'renk', 'tasarım']):
                            user_requests.append(f"{created_at}: {content[:200]}...")
    except Exception as e:
        pass

user_requests.sort()
print(f"Found {len(user_requests)} UI-related requests.")
for r in user_requests[-10:]:
    print(r)

