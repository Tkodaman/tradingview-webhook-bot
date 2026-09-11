import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'best_found.html', 'r', encoding='utf-8') as f:
    text = f.read()

for line in text.splitlines():
    if 'ko?ullar' in line:
        print(line.strip())
