import os
for f in os.listdir('templates'):
    if f.endswith('.html'):
        with open(os.path.join('templates', f), 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
            if 'FUTURE ADVANCING ENGINE' in text:
                print(f"Found in {f}")
