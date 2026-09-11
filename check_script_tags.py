with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

scripts = text.split('<script>')
print(f"Number of <script> tags: {len(scripts)-1}")
for i, s in enumerate(scripts[1:]):
    print(f"Script {i} length:", len(s))
