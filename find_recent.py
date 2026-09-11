import json
import glob
import os
import datetime

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

file_info = []
for f in files:
    mtime = os.path.getmtime(f)
    dt = datetime.datetime.fromtimestamp(mtime)
    file_info.append((f, dt))

file_info.sort(key=lambda x: x[1])

for f, dt in file_info[-15:]:
    print(dt.strftime('%Y-%m-%d %H:%M:%S'), f)
