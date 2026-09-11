import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
cands = glob.glob('templates/cand_*.html')
for c in cands:
    uid = c.split('_')[-1].split('.')[0]
    # find the full path
    files = glob.glob(os.path.join(brain_dir, f'*{uid}*', '.system_generated', 'logs', '*full.jsonl'))
    if files:
        mtime = os.path.getmtime(files[0])
        import datetime
        dt = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{dt} - {c} - Size: {os.path.getsize(c)}")
