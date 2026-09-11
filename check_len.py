import json
import glob
import os

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                if '<!DOCTYPE html>' in line:
                    data = json.loads(line)
                    if 'content' in data:
                        c = data['content']
                        if type(c) == str and '<!DOCTYPE html>' in c:
                            print("FOUND html in", f[-50:], "length:", len(c), "Ends with html?", '</html>' in c)
    except Exception as e:
        pass
